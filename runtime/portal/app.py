import hmac
import os
import re
import secrets
import subprocess
import shutil
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup
import bleach
import markdown

from zip_upload import extract_archive

PROJECTS = Path(os.environ.get("REVERSA_PROJECTS", "/home/opc/proyectos")).resolve()
SECRET = Path(os.environ.get("REVERSA_PORTAL_SECRET", "/home/opc/.config/reversa-portal/session.key"))
app = Flask(__name__)
app.secret_key = SECRET.read_text().strip()
app.config.update(
    MAX_CONTENT_LENGTH=105 * 1024 * 1024,
    SESSION_COOKIE_NAME="reversa_portal",
    SESSION_COOKIE_PATH="/proyectos/",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1, x_proto=1)

OUTPUT_DIRS = ("_reversa_sdd", "_reversa_docs", "_reversa_forward")
PREVIEW_LIMIT = 2 * 1024 * 1024
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".mmd", ".puml", ".xml", ".html", ".css", ".js", ".svg", ".log"}
SITE_MIMES = {".html": "text/html", ".htm": "text/html", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf"}


def safe_path(root, relative):
    """Reject traversal, hidden components and symlinks, including intermediate ones."""
    parts = relative.split("/")
    if any(not p or p.startswith(".") or "\\" in p or ":" in p or "\x00" in p for p in parts):
        abort(404)
    target = root
    for part in parts:
        target = target / part
        if target.is_symlink():
            abort(404)
    if not target.resolve().is_relative_to(root.resolve()):
        abort(404)
    return target


def project_path(name):
    target = safe_path(PROJECTS, name)
    if "/" in name or not target.is_dir():
        abort(404)
    return target


def result_path(name, relative):
    project = project_path(name)
    if relative.split("/")[0] not in OUTPUT_DIRS:
        abort(404)
    return safe_path(project, relative)


def output_available(root, folder):
    target = root / folder
    return not target.is_symlink() and target.is_dir() and any(
        not child.name.startswith(".") and not child.is_symlink()
        for child in target.iterdir()
    )


@app.get("/proyecto/<name>/")
@app.get("/proyecto/<name>/resultados/<path:relative>")
def project(name, relative=None):
    root = project_path(name)
    session.setdefault("csrf", secrets.token_urlsafe(32))
    view = request.args.get("vista", "resumen")
    if view not in {"resumen", "analisis", "html", "archivos"}:
        abort(404)
    selected = relative
    if not selected and view == "analisis":
        selected = "_reversa_sdd"
    elif not selected and view == "html":
        selected = "_reversa_docs"
    target = result_path(name, selected) if selected else root
    if relative and not target.exists():
        abort(404)
    if relative:
        view = {"_reversa_sdd": "analisis", "_reversa_docs": "html"}.get(relative.split("/")[0], "archivos")
    if not relative and view == "html" and target.is_dir():
        index = target / "index.html"
        if index.is_file() and not index.is_symlink():
            target = index
            selected = index.relative_to(root).as_posix()
    entries, content, rendered, note = [], None, None, None
    site_url = None
    if target.is_dir():
        children = target.iterdir() if selected else (root / folder for folder in OUTPUT_DIRS)
        for child in children:
            if child.name.startswith(".") or child.is_symlink() or not child.exists():
                continue
            if not child.is_dir() and not child.is_file():
                continue
            entries.append({"name": child.name, "relative": child.relative_to(root).as_posix(), "directory": child.is_dir(), "size": child.stat().st_size})
        entries.sort(key=lambda row: (not row["directory"], row["name"].casefold()))
    elif target.is_file():
        if selected.startswith("_reversa_docs/") and target.suffix.lower() in {".html", ".htm"}:
            site_url = url_for("site", name=name, relative=target.relative_to(root / "_reversa_docs").as_posix())
        if target.suffix.lower() in TEXT_SUFFIXES and target.stat().st_size <= PREVIEW_LIMIT:
            try:
                content = target.read_bytes()[:PREVIEW_LIMIT + 1].decode("utf-8-sig")
                if "\x00" in content or len(content.encode("utf-8")) > PREVIEW_LIMIT:
                    content = None
            except UnicodeDecodeError:
                content = None
        if content is None:
            note = "Vista previa no disponible: descarga el archivo. El visor admite texto UTF-8 de hasta 2 MiB."
        elif target.suffix.lower() in {".md", ".markdown"}:
            html = markdown.markdown(content, extensions=["tables", "fenced_code", "sane_lists"])
            rendered = Markup(bleach.clean(html, tags={"p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "strong", "em", "blockquote", "pre", "code", "a", "table", "thead", "tbody", "tr", "th", "td", "del"}, attributes={"a": ["href", "title"], "ol": ["start"]}, protocols=["http", "https", "mailto"], strip=True))
    elif target.exists():
        abort(404)
    crumbs = []
    if selected:
        parts = selected.split("/")
        crumbs = [{"name": part, "relative": "/".join(parts[:i + 1])} for i, part in enumerate(parts)]
    return render_template("project.html", name=name, relative=selected, entries=entries, content=content,
                           rendered=rendered, note=note, crumbs=crumbs, is_file=target.is_file(), view=view,
                           overview=not relative and view == "resumen", site_url=site_url,
                           refresh_relative=selected if target.exists() else None,
                           has_analysis=output_available(root, "_reversa_sdd"), has_html=output_available(root, "_reversa_docs"))


@app.get("/proyecto/<name>/sitio/<path:relative>")
def site(name, relative):
    target = result_path(name, "_reversa_docs/" + relative.rstrip("/"))
    if target.is_dir():
        if not request.path.endswith("/"):
            return redirect(url_for("site", name=name, relative=relative + "/"))
        target = result_path(name, "_reversa_docs/" + relative.rstrip("/") + "/index.html")
    mime = SITE_MIMES.get(target.suffix.lower())
    if not target.is_file() or not mime:
        abort(404)
    return send_file(target, mimetype=mime, conditional=False)


@app.get("/proyecto/<name>/descargar/<path:relative>")
def download(name, relative):
    target = result_path(name, relative)
    if not target.is_file():
        abort(404)
    return send_file(target, as_attachment=True, download_name=target.name, mimetype="application/octet-stream", conditional=False)


@app.after_request
def headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'none'; frame-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
    if request.endpoint == "site":
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "sandbox; default-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; script-src 'none'; frame-ancestors 'self'; form-action 'none'; base-uri 'none'"
    return response


@app.get("/")
def home():
    session.setdefault("csrf", secrets.token_urlsafe(32))
    rows = []
    for path in sorted(PROJECTS.iterdir()):
        if path.is_symlink() or not path.is_dir() or path.name.startswith("."):
            continue
        rows.append({"name": path.name, "path": str(path), "analysis": output_available(path, "_reversa_sdd"), "html": output_available(path, "_reversa_docs")})
    return render_template("index.html", projects=rows)


@app.post("/crear")
def create():
    token = request.form.get("csrf", "")
    if not session.get("csrf") or not hmac.compare_digest(token, session["csrf"]):
        flash("La sesión del formulario venció. Recarga la página y vuelve a intentarlo.", "error")
        return redirect(url_for("home"))
    name = request.form.get("name", "").strip().lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", name):
        flash("Usa un nombre de hasta 64 caracteres: letras sin acentos, números y guiones.", "error")
        return redirect(url_for("home"))
    target = PROJECTS / name
    if target.exists() or target.is_symlink():
        flash("Ese proyecto ya existe. Elige otro nombre.", "error")
        return redirect(url_for("home"))
    upload = request.files.get("archive")
    if not upload or not upload.filename or not upload.filename.lower().endswith(".zip"):
        flash("Selecciona un archivo ZIP con el código del proyecto.", "error")
        return redirect(url_for("home"))
    stage = Path(tempfile.mkdtemp(prefix=".upload-", dir=PROJECTS))
    archive_path = stage / "upload.zip"
    source = stage / "source"
    source.mkdir()
    reserved = False
    try:
        upload.save(archive_path)
        if archive_path.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("El ZIP supera los 100 MiB.")
        count = extract_archive(archive_path, source)
        # mkdir is exclusive: concurrent uploads cannot overwrite one another.
        target.mkdir(mode=0o700)
        reserved = True
        for child in source.iterdir():
            child.rename(target / child.name)
        init_command = os.environ.get("REVERSA_INIT_COMMAND")
        if init_command:
            result = subprocess.run([init_command, str(target)], capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                app.logger.error("Inicialización Reversa: %s", result.stderr)
                raise RuntimeError("No se pudo preparar Reversa. El administrador debe revisar el registro del portal.")
        flash(f"Proyecto {name} creado con {count} archivos. Ábrelo en OpenCode y ejecuta /reversa.", "success")
    except (ValueError, zipfile.BadZipFile, NotImplementedError, RuntimeError, subprocess.TimeoutExpired) as error:
        if reserved:
            shutil.rmtree(target)
        flash(str(error), "error")
    except FileExistsError:
        if reserved:
            shutil.rmtree(target)
        flash("La carga contiene rutas incompatibles o el proyecto ya existe.", "error")
    except OSError:
        if reserved:
            shutil.rmtree(target)
        app.logger.exception("Error al guardar proyecto")
        flash("No se pudo guardar la carga. Revisa el espacio disponible y los registros del servicio.", "error")
    finally:
        shutil.rmtree(stage)
    return redirect(url_for("home"))


@app.post("/proyecto/<name>/cargar")
def upload_files(name):
    target = project_path(name)
    token = request.form.get("csrf", "")
    if not session.get("csrf") or not hmac.compare_digest(token, session["csrf"]):
        abort(400, "La sesión del formulario venció. Recarga y vuelve a intentarlo.")
    upload = request.files.get("archive")
    if not upload or not upload.filename or not upload.filename.lower().endswith(".zip"):
        flash("Selecciona un ZIP con los archivos adicionales.", "error")
        return redirect(url_for("project", name=name))
    stage = Path(tempfile.mkdtemp(prefix=".upload-", dir=PROJECTS))
    created = []
    try:
        archive_path, source = stage / "upload.zip", stage / "source"
        source.mkdir()
        upload.save(archive_path)
        if archive_path.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("El ZIP supera los 100 MiB.")
        count = extract_archive(archive_path, source)
        planned = []
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            if relative.parts[0] in OUTPUT_DIRS:
                raise ValueError("Carga los archivos de entrada fuera de las carpetas de resultados.")
            destination = target / relative
            for ancestor in [destination, *destination.parents]:
                if ancestor == target:
                    break
                if ancestor.is_symlink() or (ancestor != destination and ancestor.exists() and not ancestor.is_dir()):
                    raise ValueError("La carga contiene una ruta incompatible.")
            if destination.exists():
                raise ValueError("La carga contiene archivos existentes. Renómbralos antes de subirlos; no se sobrescribe ningún archivo.")
            planned.append((path, destination))
        for path, destination in planned:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as output:
                created.append(destination)
                with path.open("rb") as input_file:
                    shutil.copyfileobj(input_file, output)
            destination.chmod(0o600)
        flash(f"Se agregaron {count} archivos a {name}.", "success")
    except (ValueError, zipfile.BadZipFile, NotImplementedError, RuntimeError, OSError) as error:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        app.logger.info("Carga adicional rechazada: %s", type(error).__name__)
        flash(str(error) if isinstance(error, ValueError) else "No se pudo completar la carga. Verifica el ZIP y el espacio disponible.", "error")
    finally:
        shutil.rmtree(stage)
    return redirect(url_for("project", name=name))


@app.errorhandler(413)
def too_large(error):
    return render_template("error.html", message="La carga es demasiado grande. El ZIP debe ser de hasta 100 MiB."), 413
