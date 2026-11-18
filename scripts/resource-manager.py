"""Operate an EXISTING Resource Manager stack with an OCI temporary session.

Keeps the state in Resource Manager. Never runs a local Terraform apply.
"""
import argparse
import base64
import json
import os
import time
from pathlib import Path
import oci

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status','sync-source','plan','apply','outputs','logs'])
    parser.add_argument('--config', default=str(ROOT/'local/oci/config'))
    parser.add_argument('--profile', default='REVERSA')
    parser.add_argument('--refs', type=Path, default=ROOT/'local/deployment.private.json')
    parser.add_argument('--job-id')
    parser.add_argument('--plan-id')
    parser.add_argument('--variables', type=Path)
    parser.add_argument('--wait', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    refs = json.loads(args.refs.read_text())
    config = oci.config.from_file(args.config, args.profile)
    if config['tenancy'] != refs['tenancy_ocid']:
        raise RuntimeError('La sesión pertenece a otro tenant. Cero cambios.')
    config['region'] = refs['region']
    token = Path(config['security_token_file']).expanduser().read_text()
    private_key = oci.signer.load_private_key_from_file(config['key_file'], config.get('pass_phrase'))
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    rm = oci.resource_manager.ResourceManagerClient(config, signer=signer)
    response = rm.get_stack(refs['stack_ocid'])
    stack = response.data
    if stack.variables.get('tenancy_ocid') != refs['tenancy_ocid']:
        raise RuntimeError('El stack no corresponde al tenant esperado. Cero cambios.')

    def save():
        args.refs.write_text(json.dumps(refs,indent=2)+'\n')
        args.refs.chmod(0o600)

    def job_summary(job):
        return {'job_id':job.id,'name':job.display_name,'operation':job.operation,'state':job.lifecycle_state}

    def active_jobs():
        jobs = oci.pagination.list_call_get_all_results(
            rm.list_jobs, compartment_id=stack.compartment_id, stack_id=stack.id).data
        return [j for j in jobs if j.lifecycle_state in {'ACCEPTED','IN_PROGRESS','CANCELING'}]

    if args.action == 'status':
        jobs = oci.pagination.list_call_get_all_results(
            rm.list_jobs,compartment_id=stack.compartment_id,stack_id=stack.id).data
        print(json.dumps([job_summary(j) for j in jobs[:8]],indent=2))
        return
    if args.action == 'logs':
        import re
        job = rm.get_job(args.job_id or refs['plan_job_ocid']).data
        if job.stack_id != stack.id:
            raise RuntimeError('El job no pertenece al stack esperado')
        content = rm.get_job_logs_content(job.id).data.content
        log = ROOT/'local'/('reversa-'+job.operation.lower()+'.private.log')
        log.write_bytes(content)
        log.chmod(0o600)
        clean = re.sub(r'\x1b\[[0-9;]*m','',content.decode('utf-8',errors='replace'))
        summary = re.findall(r'(?:Plan: \d+ to add, \d+ to change, \d+ to destroy\.|Apply complete![^\n]*)',clean)
        print(json.dumps({'job':job_summary(job),'summary':summary,'log_file':str(log)},indent=2))
        return
    if args.action == 'sync-source':
        if active_jobs(): raise RuntimeError('Hay un job activo; esperar antes de cambiar código/variables.')
        variables = dict(stack.variables)
        if args.variables:
            update = json.loads(args.variables.read_text())
            allowed = {'genai_api_key_ocid','genai_secret_ocid','web_secret_ocid','image_ocid',
                       'availability_domain','enable_compute','ssh_public_key','bastion_allowed_cidrs'}
            if not set(update) <= allowed:
                raise RuntimeError('Variables no permitidas para actualización de runtime')
            for name,value in update.items():
                variables[name] = value if isinstance(value,str) else json.dumps(value)
        source = oci.resource_manager.models.UpdateZipUploadConfigSourceDetails(
            zip_file_base64_encoded=base64.b64encode((ROOT/'reversa-resource-manager.zip').read_bytes()).decode())
        rm.update_stack(stack.id,oci.resource_manager.models.UpdateStackDetails(
            config_source=source,variables=variables),if_match=response.headers['etag'])
        refs['stack_source_needs_update'] = False
        save()
        print('Código y variables actualizados en el mismo stack; no se ejecutó Apply.')
        return
    if args.action == 'outputs':
        job_id = args.job_id or refs.get('apply_job_ocid')
        job = rm.get_job(job_id).data
        if job.stack_id != stack.id or job.operation != 'APPLY' or job.lifecycle_state != 'SUCCEEDED':
            raise RuntimeError('Solo se exportan salidas de un Apply exitoso del mismo stack')
        data = json.loads(rm.get_job_tf_state(job.id).data.content)
        out = ROOT/'local/outputs.json'
        out.write_text(json.dumps(data['outputs'],indent=2)+'\n')
        out.chmod(0o600)
        print('Salidas guardadas localmente. Valores secretos no forman parte de este estado.')
        return
    if active_jobs(): raise RuntimeError('Ya hay un job activo; consultar status, no duplicarlo.')
    if args.action == 'plan':
        details = oci.resource_manager.models.PlanJobOperationDetails()
        operation = 'PLAN'
    else:
        plan = rm.get_job(args.plan_id or refs['plan_job_ocid']).data
        if plan.stack_id != stack.id or plan.operation != 'PLAN' or plan.lifecycle_state != 'SUCCEEDED':
            raise RuntimeError('Apply requiere un Plan exitoso del mismo stack')
        details = oci.resource_manager.models.ApplyJobOperationDetails(
            execution_plan_strategy='FROM_PLAN_JOB_ID', execution_plan_job_id=plan.id)
        operation = 'APPLY'
    job = rm.create_job(oci.resource_manager.models.CreateJobDetails(
        stack_id=stack.id,display_name='reversa-'+operation.lower()+'-'+str(int(time.time())),
        operation=operation,job_operation_details=details)).data
    refs['plan_job_ocid' if operation == 'PLAN' else 'apply_job_ocid'] = job.id
    if operation == 'APPLY': refs['apply_submitted'] = True
    save()
    print(json.dumps(job_summary(job)),flush=True)
    if args.wait:
        last = job.lifecycle_state
        while job.lifecycle_state in {'ACCEPTED','IN_PROGRESS','CANCELING'}:
            time.sleep(15)
            job = rm.get_job(job.id).data
            if job.lifecycle_state != last:
                print(json.dumps(job_summary(job)),flush=True)
                last = job.lifecycle_state
        refs['last_observed_state'] = job.lifecycle_state
        save()
        if job.lifecycle_state != 'SUCCEEDED': raise RuntimeError('El job no terminó correctamente; conservar el mismo estado.')


if __name__ == '__main__':
    main()
