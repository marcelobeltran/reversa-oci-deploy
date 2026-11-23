"""Guided bridge between Resource Manager console phases. No Terraform apply.

Uses Cloud Shell's delegated user session. Prepares credentials and references
only after a successful VM-free foundation apply; the user runs plans in OCI.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import oci

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = {'ACCEPTED', 'IN_PROGRESS', 'CANCELING'}
class SetupError(RuntimeError):
    pass


ALLOWED = {'genai_api_key_ocid', 'genai_secret_ocid', 'web_secret_ocid',
           'image_ocid', 'availability_domain', 'ssh_public_key'}


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    path.chmod(0o600)


def cloud_auth(region):
    location = os.environ.get('OCI_CLI_CONFIG_FILE', '/etc/oci/config')
    profile = os.environ.get('OCI_CLI_PROFILE', region)
    config = oci.config.from_file(location, profile)
    token_file = os.environ.get('OCI_CLI_DELEGATION_TOKEN_FILE') or config.get('delegation_token_file')
    if not token_file:
        raise SetupError('Abre OCI Cloud Shell: falta su sesión delegada. No se necesitan claves IAM de usuario.')
    signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
        delegation_token=Path(token_file).expanduser().read_text().strip())
    config['region'] = region
    return config, signer


def check_stack(config, stack):
    if stack.variables.get('tenancy_ocid') != config['tenancy']:
        raise SetupError('El stack y la sesión pertenecen a tenants distintos. Cero cambios.')
    if stack.variables.get('region', 'us-chicago-1') != config['region']:
        raise SetupError('La región del stack y la seleccionada no coinciden. Cero cambios.')
    prefix = stack.variables.get('prefix', 'reversa')
    if not re.fullmatch(r'reversa[a-z0-9-]{0,23}', prefix):
        raise SetupError('Prefijo inesperado. Debe empezar por reversa y tener hasta 30 caracteres.')
    return prefix


def job_outputs(rm, stack):
    jobs = oci.pagination.list_call_get_all_results(
        rm.list_jobs, compartment_id=stack.compartment_id, stack_id=stack.id).data
    if any(j.lifecycle_state in ACTIVE for j in jobs):
        raise SetupError('Hay un job activo. Espera su resultado en Resource Manager y repite este comando.')
    applies = [j for j in jobs if j.operation == 'APPLY']
    if not applies:
        raise SetupError('Primero ejecuta Plan y Apply de la base en Resource Manager.')
    latest = max(applies, key=lambda j: j.time_created)
    if latest.lifecycle_state != 'SUCCEEDED':
        raise SetupError('El último Apply no terminó SUCCEEDED. Resuélvelo en el mismo stack antes de continuar.')
    raw = rm.get_job_tf_state(latest.id).data
    if hasattr(raw, 'content'):
        raw = raw.content
    return json.loads(raw)['outputs']


def require_no_vm(stack, outputs):
    if str(stack.variables.get('enable_compute', 'false')).lower() != 'false':
        raise SetupError('La VM está habilitada: prepare solo sirve antes de la primera VM. No se deshabilitará.')
    if outputs.get('instance_ocid', {}).get('value'):
        raise SetupError('El estado ya contiene una VM. No repetir la preparación inicial.')


def sync_references(rm, stack_id, config, variables):
    if not set(variables) <= ALLOWED:
        raise SetupError('Solo se permiten referencias de runtime y la clave SSH pública.')
    response = rm.get_stack(stack_id)
    stack = response.data
    check_stack(config, stack)
    # Recheck after credential creation: another operator may have changed the stack.
    require_no_vm(stack, job_outputs(rm, stack))
    merged = dict(stack.variables)
    merged.update(variables)
    rm.update_stack(stack.id, oci.resource_manager.models.UpdateStackDetails(
        variables=merged), if_match=response.headers['etag'])


def ensure_ssh_key():
    key = ROOT/'local/reversa-admin'
    public = Path(str(key)+'.pub')
    if key.exists() != public.exists():
        raise SetupError('Par SSH incompleto en local/. Recupera la clave y su .pub; no se sobrescriben.')
    if not key.exists():
        subprocess.run(['ssh-keygen', '-t', 'ed25519', '-N', '', '-f', str(key),
                        '-C', 'reversa-admin'], check=True, capture_output=True)
        key.chmod(0o600)
    value = public.read_text().strip()
    if not value.startswith('ssh-ed25519 '):
        raise SetupError('La clave administrativa no tiene el formato Ed25519 esperado.')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'check'])
    parser.add_argument('--stack-id')
    parser.add_argument('--region', default='us-chicago-1')
    args = parser.parse_args()
    os.umask(0o077)
    config, signer = cloud_auth(args.region)
    rm = oci.resource_manager.ResourceManagerClient(config, signer=signer)
    context_path = ROOT/'local/cloud-shell.private.json'
    previous = json.loads(context_path.read_text()) if context_path.exists() else None
    stack_id = args.stack_id or (previous or {}).get('stack_ocid')
    if not stack_id:
        stack_id = input('Pega el OCID del stack reversa creado en Resource Manager: ').strip()
    if not stack_id.startswith('ocid1.ormstack.'):
        raise SetupError('Se espera un OCID de stack, no de tenant ni de identity domain.')
    context = {'tenancy_ocid': config['tenancy'], 'region': args.region, 'stack_ocid': stack_id}
    if previous and previous != context:
        raise SetupError('Esta carpeta pertenece a otro stack/tenant. Extrae el ZIP en otra carpeta vacía.')
    stack = rm.get_stack(stack_id).data
    prefix = check_stack(config, stack)
    outputs = job_outputs(rm, stack)
    if args.action == 'prepare':
        require_no_vm(stack, outputs)
    scope = {'ai': outputs['compartments']['value']['ai'],
             'security': outputs['compartments']['value']['security'],
             'vault': outputs['vault']['value']['id']}
    checkpoint = ROOT/'local/runtime.private.json'
    if checkpoint.exists() and json.loads(checkpoint.read_text()).get('scope') != scope:
        raise SetupError('El checkpoint de credenciales pertenece a otros recursos. Cero cambios.')
    if args.action == 'check' and not previous:
        raise SetupError('Primero completa prepare en esta carpeta después de aplicar la base.')
    save(context_path, context)
    save(ROOT/'local/outputs.json', outputs)
    if args.action == 'prepare':
        print('1/3 Tenant y stack verificados. Base aplicada, sin VM.', flush=True)
        if not hasattr(oci.generative_ai.models, 'CreateApiKeyDetails'):
            raise SetupError('SDK OCI antiguo: sigue la sección de actualización del SDK en la guía Cloud Shell.')
        public_key = ensure_ssh_key()
        subprocess.run([sys.executable, str(ROOT/'scripts/prepare-runtime.py'),
                        '--outputs', 'local/outputs.json', '--auth', 'cloud_shell',
                        '--region', args.region, '--prefix', prefix], cwd=ROOT, check=True)
        variables_path = ROOT/'local/runtime.auto.tfvars.json'
        variables = json.loads(variables_path.read_text())
        variables['ssh_public_key'] = public_key
        print('2/3 Secretos en Vault y clave SSH administrativa preparada. Valores privados no impresos.', flush=True)
        sync_references(rm, stack_id, config, variables)
        save(variables_path, variables)
        print('3/3 Referencias actualizadas en el MISMO stack. No se ejecutó Plan/Apply ni se creó una VM.')
        print('SIGUIENTE: en Resource Manager ejecuta Plan y Apply de IAM con enable_compute=false.')
        print('Cuando termine SUCCEEDED, aquí ejecuta: python3 scripts/cloud-shell.py check')
    else:
        private = json.loads(checkpoint.read_text())
        if private['api_key']['id'] != stack.variables.get('genai_api_key_ocid'):
            raise SetupError('La clave del checkpoint no coincide con la referencia del stack.')
        print('Probando una inferencia pequeña real a OCI GenAI (puede generar consumo).', flush=True)
        subprocess.run([sys.executable, str(ROOT/'scripts/smoke-genai.py'),
                        '--region', args.region, '--model', stack.variables.get('model_id', 'xai.grok-4.6')],
                       cwd=ROOT, check=True)
        print('SIGUIENTE: en Resource Manager cambia enable_compute=true, revisa Plan y ejecuta Apply.')


if __name__ == '__main__':
    try:
        main()
    except SetupError as error:
        raise SystemExit(str(error)) from None
    except oci.exceptions.ServiceError as error:
        raise SystemExit('OCI '+str(error.status)+' '+str(error.code)+'. Revisa permisos, región y sesión Cloud Shell. No se imprimen cuerpos de API.') from None
    except Exception as error:
        raise SystemExit('Proceso detenido ('+type(error).__name__+'). Conserva local/ y revisa la guía; no se imprimen secretos.') from None
