"""Build deterministic runtime and Resource Manager ZIP from an explicit allowlist."""
import gzip
import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w') as tar:
    for path in sorted((ROOT/'runtime').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            data = path.read_bytes()
            if path.suffix in {'.py', '.sh', '.mjs', '.json', '.conf', '.service', '.timer', '.txt', '.html', '.css', '.js'}:
                data = data.replace(b'\r\n', b'\n')
            info = tarfile.TarInfo(path.relative_to(ROOT/'runtime').as_posix())
            info.size = len(data)
            info.mode = 0o755 if path.suffix in {'.sh', '.mjs'} else 0o644
            info.mtime = 0
            tar.addfile(info, io.BytesIO(data))
runtime = gzip.compress(buf.getvalue(), mtime=0)
(ROOT/'runtime.tar.gz').write_bytes(runtime)
allowed = [*ROOT.glob('*.tf'), ROOT/'cloud-init.yaml.tftpl', ROOT/'runtime.tar.gz', ROOT/'.terraform.lock.hcl']
target = ROOT/'reversa-resource-manager.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(allowed):
        if path.exists():
            archive.writestr(path.name, path.read_bytes())
print(json.dumps({'runtime_bytes':len(runtime), 'stack_bytes':target.stat().st_size,
                  'stack_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}, indent=2))
