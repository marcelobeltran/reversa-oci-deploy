"""Run with a signed-in OCI SDK profile after the foundation apply.

Creates a service-specific GenAI key and stores both runtime secrets directly in
Vault. Values never enter Terraform state, command arguments, stdout or Git.
Maintains a private checkpoint so retries don't issue another key. Existing
untracked credentials cause an abort rather than silent duplication.
"""
import argparse
import base64
import datetime as dt
import json
import os
import secrets
from pathlib import Path
import oci


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, indent=2)+'\n')
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outputs', required=True, type=Path, help='terraform output -json file')
    parser.add_argument('--profile', default='DEFAULT')
    parser.add_argument('--config', default='~/.oci/config')
    parser.add_argument('--auth', choices=['api_key','security_token','cloud_shell'], default='api_key')
    parser.add_argument('--region', default='us-chicago-1')
    parser.add_argument('--prefix', default='reversa')
    parser.add_argument('--checkpoint', type=Path, default=Path('local/runtime.private.json'))
    parser.add_argument('--variables', type=Path, default=Path('local/runtime.auto.tfvars.json'))
    args = parser.parse_args()
    os.umask(0o077)
    out = {k:v['value'] for k,v in json.loads(args.outputs.read_text()).items()}
    config_file = os.environ.get('OCI_CLI_CONFIG_FILE', args.config) if args.auth == 'cloud_shell' else args.config
    profile = os.environ.get('OCI_CLI_PROFILE', args.profile) if args.auth == 'cloud_shell' else args.profile
    config = oci.config.from_file(file_location=str(Path(config_file).expanduser()), profile_name=profile)
    config['region'] = args.region
    kwargs = {}
    if args.auth == 'security_token':
        token = Path(config['security_token_file']).expanduser().read_text()
        private_key = oci.signer.load_private_key_from_file(config['key_file'], config.get('pass_phrase'))
        kwargs['signer'] = oci.auth.signers.SecurityTokenSigner(token, private_key)
    elif args.auth == 'cloud_shell':
        token_file = os.environ.get('OCI_CLI_DELEGATION_TOKEN_FILE') or config.get('delegation_token_file')
        if not token_file:
            raise RuntimeError('Ejecutar desde OCI Cloud Shell con su sesión delegada activa')
        kwargs['signer'] = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
            delegation_token=Path(token_file).expanduser().read_text().strip())
    ai = oci.generative_ai.GenerativeAiClient(config, **kwargs)
    vault = oci.vault.VaultsClient(config, **kwargs)
    checkpoint = json.loads(args.checkpoint.read_text()) if args.checkpoint.exists() else {}
    scope = {'ai':out['compartments']['ai'], 'security':out['compartments']['security'], 'vault':out['vault']['id']}
    if checkpoint and checkpoint.get('scope') != scope:
        raise RuntimeError('El checkpoint pertenece a otro tenant/compartimento; usar otra carpeta local')
    checkpoint['scope'] = scope

    def stash(): save(args.checkpoint, checkpoint)

    if not checkpoint.get('api_key'):
        existing = oci.pagination.list_call_get_all_results(ai.list_api_keys, compartment_id=scope['ai']).data
        items = existing.items if hasattr(existing, 'items') and not isinstance(existing, list) else existing
        if any(k.display_name == args.prefix+'-genai-key' for k in items):
            raise RuntimeError('Ya hay una API key sin checkpoint; recuperarla antes de crear otra')
        # Record the new key before making subsequent API calls. This private
        # checkpoint is deliberately excluded from all packages and Git.
        expiry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=90)
        result = ai.create_api_key(oci.generative_ai.models.CreateApiKeyDetails(
            compartment_id=scope['ai'], display_name=args.prefix+'-genai-key',
            key_details=[oci.generative_ai.models.KeyDetails(key_name='reversa-active', time_expiry=expiry),
                         oci.generative_ai.models.KeyDetails(key_name='reversa-standby', time_expiry=expiry)]
        )).data
        checkpoint['api_key'] = oci.util.to_dict(result)
        stash()

    def store_secret(label, content):
        marker = label+'_secret_ocid'
        if checkpoint.get(marker): return checkpoint[marker]
        name = args.prefix+'-'+label
        existing = oci.pagination.list_call_get_all_results(vault.list_secrets, compartment_id=scope['security'], name=name).data
        if existing:
            if len(existing) != 1 or existing[0].vault_id != scope['vault']:
                raise RuntimeError('Secretos existentes ambiguos: '+name)
            checkpoint[marker] = existing[0].id
            stash()
            return existing[0].id
        result = vault.create_secret(oci.vault.models.CreateSecretDetails(
            compartment_id=scope['security'], vault_id=scope['vault'],
            key_id=out['vault']['key_id'], secret_name=name,
            secret_content=oci.vault.models.Base64SecretContentDetails(
                content=base64.b64encode(content.encode()).decode(), stage='CURRENT')
        )).data
        checkpoint[marker] = result.id
        stash()
        return result.id

    key = checkpoint['api_key']
    genai_secret = store_secret('genai', key['keys'][0]['key'])
    if 'web' not in checkpoint:
        checkpoint['web'] = {'username':'reversa', 'password':secrets.token_urlsafe(32)}
        stash()
    web_secret = store_secret('web', json.dumps(checkpoint['web']))
    compute = oci.core.ComputeClient(config, **kwargs)
    identity = oci.identity.IdentityClient(config, **kwargs)
    images = oci.pagination.list_call_get_all_results(
        compute.list_images, compartment_id=out['compartments']['app'],
        operating_system='Canonical Ubuntu', operating_system_version='24.04',
        shape='VM.Standard.E5.Flex', sort_by='TIMECREATED', sort_order='DESC').data
    images = [image for image in images if image.lifecycle_state == 'AVAILABLE']
    domains = identity.list_availability_domains(config['tenancy']).data
    if not images or not domains:
        raise RuntimeError('No hay imagen Ubuntu 24.04 E5 disponible o AD visible')
    save(args.variables, {'genai_api_key_ocid':key['id'], 'genai_secret_ocid':genai_secret,
                         'web_secret_ocid':web_secret, 'image_ocid':images[0].id,
                         'availability_domain':domains[0].name})
    print('Credenciales creadas y guardadas en Vault; variables sin secretos en '+str(args.variables))
    print('La clave GenAI vence en 90 días: renovar una de sus dos claves antes de esa fecha.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # OCI exception bodies or failed call arguments may contain secrets.
        raise SystemExit('Preparación interrumpida ('+type(error).__name__+'). Revisar acceso/SDK/checkpoint; no imprimir secretos.') from None
