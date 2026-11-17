"""Fetch Vault secrets by instance principal. Never print their values."""
import base64
import json
import os
import pwd
import secrets
import subprocess
import time
from pathlib import Path
import oci


def get_secret(secret_id):
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    client = oci.secrets.SecretsClient({}, signer=signer)
    result = client.get_secret_bundle(secret_id, stage="CURRENT").data
    return base64.b64decode(result.secret_bundle_content.content).decode().strip()


def write_private(path, content, user="opc"):
    target = Path(path)
    target.write_text(content)
    target.chmod(0o600)
    account = pwd.getpwnam(user)
    os.chown(target, account.pw_uid, account.pw_gid)


def configure():
    cfg = json.loads(Path('/etc/reversa/config.json').read_text())
    # IAM propagation is eventual. Retry only reads, never issue new credentials.
    for attempt in range(30):
        try:
            web = json.loads(get_secret(cfg['web_secret_ocid']))
            break
        except Exception:
            if attempt == 29:
                raise RuntimeError('Vault no disponible tras esperar propagación IAM') from None
            time.sleep(20)
    if not web['username'].replace('-', '').replace('_', '').isalnum() or len(web['password']) < 20:
        raise ValueError('Credenciales web inválidas: usuario simple y password >=20 caracteres')
    hashed = subprocess.run(['htpasswd', '-niB', web['username']], input=web['password']+'\n',
                            text=True, capture_output=True, check=True).stdout
    Path('/etc/nginx/reversa.htpasswd').write_text(hashed)
    Path('/etc/nginx/reversa.htpasswd').chmod(0o640)
    import grp
    os.chown('/etc/nginx/reversa.htpasswd', 0, grp.getgrnam('www-data').gr_gid)
    config = {
        '$schema': 'https://opencode.ai/config.json',
        'enabled_providers': ['oci'],
        'model': 'oci/'+cfg['model_id'],
        'small_model': 'oci/'+cfg['model_id'],
        'provider': {'oci': {
            'npm': '@ai-sdk/openai-compatible',
            'name': 'Reversa OCI directo',
            'options': {
                'baseURL': f"https://inference.generativeai.{cfg['region']}.oci.oraclecloud.com/openai/v1",
                'apiKey': '{env:OCI_API_KEY}',
                'headers': {'OpenAI-Project': cfg['genai_project_ocid']},
            },
            'models': {cfg['model_id']: {
                'id': cfg['model_id'], 'name': cfg['model_id'],
                'limit': {'context': cfg['model_context'], 'output': cfg['model_output']},
            }},
        }},
    }
    write_private('/home/opc/.config/opencode/opencode.json', json.dumps(config, indent=2)+'\n')
    secret_file = Path('/home/opc/.config/reversa-portal/session.key')
    if not secret_file.exists():
        write_private(secret_file, secrets.token_hex(32)+'\n')


if __name__ == '__main__':
    configure()
