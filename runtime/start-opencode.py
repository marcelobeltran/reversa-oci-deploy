import json
import os
import pwd
from pathlib import Path
from configure import get_secret

cfg = json.loads(Path('/etc/reversa/config.json').read_text())
key = get_secret(cfg['genai_secret_ocid'])
if not key.startswith('sk-'):
    raise RuntimeError('Vault no contiene una API key GenAI válida')
env = dict(os.environ, HOME='/home/opc', USER='opc', OCI_API_KEY=key)
user = pwd.getpwnam('opc')
os.initgroups('opc', user.pw_gid)
os.setgid(user.pw_gid)
os.setuid(user.pw_uid)
os.chdir('/home/opc/proyectos')
os.execvpe('opencode', ['opencode', 'web', '--hostname', '127.0.0.1', '--port', '4096'], env)
