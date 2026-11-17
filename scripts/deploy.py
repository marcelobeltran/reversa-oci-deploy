"""Deploy both phases with an existing OCI session; no credentials in Terraform.

Example: python scripts/deploy.py --vars tenant.tfvars --apply
Run from a fresh clone, or the existing checkout whose Terraform state you own.
Never run this against a Resource Manager stack using a separate local state.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vars', required=True, type=Path)
    parser.add_argument('--profile', default='DEFAULT')
    parser.add_argument('--auth', choices=['api_key','security_token'], default='api_key')
    parser.add_argument('--region', default='us-chicago-1')
    parser.add_argument('--prefix', default='reversa')
    parser.add_argument('--terraform', default='terraform')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        print('Plan: empaquetar, aplicar base sin VM, crear claves/Vault, aplicar IAM, crear VM privada.')
        print('Usar --apply para ejecutar. Solo contra el estado de este checkout, no otro stack remoto.')
        return
    os.umask(0o077)
    os.environ['OCI_CONFIG_FILE_PROFILE'] = args.profile
    os.environ['OCI_AUTH'] = 'SecurityToken' if args.auth == 'security_token' else 'APIKey'
    os.environ['OCI_REGION'] = args.region
    def run(*cmd, output=None):
        with output.open('w') if output else open(os.devnull, 'w') as stream:
            subprocess.run(list(cmd), cwd=ROOT, check=True, stdout=stream if output else None)
    local = ROOT/'local'
    local.mkdir(exist_ok=True, mode=0o700)
    variables = str(args.vars.resolve())
    runtime = local/'runtime.auto.tfvars.json'
    # Never reapply enable_compute=false to an existing instance.
    existing = subprocess.run([args.terraform,'state','list'],cwd=ROOT,text=True,capture_output=True)
    if 'oci_core_instance.reversa' in existing.stdout:
        raise SystemExit('La VM ya está en el estado. Actualizar mediante terraform plan; no repetir primera instalación.')
    run(sys.executable, str(ROOT/'scripts/package.py'))
    run(args.terraform,'init','-input=false')
    common = ['-var-file='+variables]
    if runtime.exists(): common.append('-var-file='+str(runtime))
    run(args.terraform,'plan','-input=false',*common,'-var=enable_compute=false','-out=local/foundation.tfplan')
    run(args.terraform,'apply','-input=false','local/foundation.tfplan')
    run(args.terraform,'output','-json',output=local/'outputs.json')
    run(sys.executable,str(ROOT/'scripts/prepare-runtime.py'),'--outputs',str(local/'outputs.json'),
        '--profile',args.profile,'--auth',args.auth,'--region',args.region,'--prefix',args.prefix)
    common = ['-var-file='+variables,'-var-file='+str(runtime)]
    run(args.terraform,'plan','-input=false',*common,'-var=enable_compute=false','-out=local/iam.tfplan')
    run(args.terraform,'apply','-input=false','local/iam.tfplan')
    run(args.terraform,'plan','-input=false',*common,'-var=enable_compute=true','-out=local/application.tfplan')
    run(args.terraform,'apply','-input=false','local/application.tfplan')
    run(args.terraform,'output','url')
    print('Infraestructura aplicada. Falta verificar bootstrap, TLS, renovación y sesión funcional según docs/operations.md.')


if __name__ == '__main__':
    main()
