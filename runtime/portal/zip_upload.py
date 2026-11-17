"""Validate and extract uploaded archives without executing their contents."""
import os
import stat
import zipfile
from pathlib import Path

MAX_EXPANDED = 500 * 1024 * 1024
MAX_FILES = 10000


def extract_archive(archive_path, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        if not entries or len(entries) > MAX_FILES:
            raise ValueError("El ZIP está vacío o supera las 10.000 entradas.")
        planned = []
        seen = set()
        declared_size = 0
        for entry in entries:
            name = entry.orig_filename
            parts = name.rstrip("/").split("/")
            if (
                not name or name.startswith("/") or "\\" in name
                or any(p in ("", ".", "..") or ":" in p or "\x00" in p for p in parts)
                or len(name) > 1000 or len(parts) > 40
            ):
                raise ValueError("El ZIP contiene rutas no permitidas.")
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("El ZIP contiene enlaces o archivos especiales.")
            if entry.flag_bits & 1:
                raise ValueError("No se admiten ZIP protegidos con contraseña.")
            if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError("Utiliza un ZIP con compresión estándar (Deflate).")
            if any(p.startswith(".") for p in parts) or "__MACOSX" in parts:
                # Credentials, Git metadata and per-project agent overrides stay out.
                continue
            if any(p == "node_modules" for p in parts):
                continue
            if entry.is_dir():
                continue
            declared_size += entry.file_size
            if declared_size > MAX_EXPANDED:
                raise ValueError("El contenido descomprimido supera los 500 MiB.")
            planned.append((entry, parts))
        if not planned:
            raise ValueError("El ZIP no contiene archivos utilizables.")
        # Remove a single wrapper folder so the project opens at its source root.
        strip = all(len(parts) > 1 for _, parts in planned) and len({p[0] for _, p in planned}) == 1
        for entry, parts in planned:
            if strip:
                parts = parts[1:]
            folded = "/".join(parts).casefold()
            if folded in seen:
                raise ValueError("El ZIP contiene rutas duplicadas.")
            seen.add(folded)
        actual_size = 0
        for entry, parts in planned:
            if strip:
                parts = parts[1:]
            target = destination.joinpath(*parts)
            if not target.resolve().is_relative_to(destination):
                raise ValueError("El ZIP contiene rutas fuera del proyecto.")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, target.open("xb") as output:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    actual_size += len(chunk)
                    if actual_size > MAX_EXPANDED:
                        raise ValueError("El contenido descomprimido supera los 500 MiB.")
                    output.write(chunk)
            os.chmod(target, 0o600)
    return len(planned)
