"""Create/reuse a temporary port-forwarding session to the private VM's SSH port.

Requires an existing Bastion, local/reversa-admin.pub and exported stack outputs.
No agent plugin or public VM IP is required. Session metadata stays under local/.
"""
import argparse
import json
import time
from pathlib import Path
import oci


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='local/oci/config')
    parser.add_argument('--profile', default='REVERSA')
    args = parser.parse_args()
    config = oci.config.from_file(args.config, args.profile)
    signer = oci.auth.signers.SecurityTokenSigner(
        Path(config['security_token_file']).read_text(),
        oci.signer.load_private_key_from_file(config['key_file']))
    out = {k: v['value'] for k, v in json.loads(Path('local/outputs.json').read_text()).items()}
    client = oci.bastion.BastionClient(config, signer=signer)
    bastions = oci.pagination.list_call_get_all_results(
        client.list_bastions, compartment_id=out['compartments']['operations']).data
    bastions = [b for b in bastions if b.lifecycle_state == 'ACTIVE'
                and b.target_subnet_id == out['private_subnet_ocid']]
    if len(bastions) != 1:
        raise SystemExit('Expected exactly one active Bastion for this private subnet')
    path = Path('local/admin-session.private.json')
    session = None
    if path.exists():
        session = client.get_session(json.loads(path.read_text())['id']).data
        if session.bastion_id != bastions[0].id:
            raise SystemExit('Session belongs to a different Bastion')
        if session.lifecycle_state not in ('ACTIVE', 'CREATING'):
            session = None
    if session is None:
        session = client.create_session(oci.bastion.models.CreateSessionDetails(
            bastion_id=bastions[0].id, display_name='reversa-admin',
            session_ttl_in_seconds=3600, key_type='PUB',
            key_details=oci.bastion.models.PublicKeyDetails(
                public_key_content=Path('local/reversa-admin.pub').read_text()),
            target_resource_details=oci.bastion.models.CreatePortForwardingSessionTargetResourceDetails(
                target_resource_id=out['instance_ocid'],
                target_resource_private_ip_address=out['private_ip'], target_resource_port=22))).data
        path.write_text(json.dumps(oci.util.to_dict(session), indent=2))
        path.chmod(0o600)
    while session.lifecycle_state == 'CREATING':
        time.sleep(10)
        session = client.get_session(session.id).data
    path.write_text(json.dumps(oci.util.to_dict(session), indent=2))
    if session.lifecycle_state != 'ACTIVE':
        raise SystemExit('Bastion session did not become active: '+session.lifecycle_state)
    print('Temporary administrative session active; metadata saved privately under local/.')


if __name__ == '__main__':
    main()
