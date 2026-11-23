"""Exercise provisioning control flow with SDK models and mocked cloud clients."""
import importlib.util
import json
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SOURCE = Path(__file__).resolve().parents[1]/'scripts/prepare-runtime.py'
spec = importlib.util.spec_from_file_location('prepare_runtime', SOURCE)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class PrepareRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.outputs = self.root/'outputs.json'
        self.checkpoint = self.root/'checkpoint.json'
        self.variables = self.root/'vars.json'
        values = {'compartments': {'ai':'test-ai', 'app':'test-app', 'security':'test-security'},
                  'vault': {'id':'test-vault', 'key_id':'test-kms'}}
        self.outputs.write_text(json.dumps({k:{'value':v} for k,v in values.items()}))
        self.ai, self.vault, self.compute, self.identity = [MagicMock() for _ in range(4)]
        self.ai.create_api_key.return_value.data = types.SimpleNamespace()
        self.identity.list_availability_domains.return_value.data = [types.SimpleNamespace(name='test-ad')]
        self.created_secrets = []
        def create_secret(details):
            self.created_secrets.append(details)
            return types.SimpleNamespace(data=types.SimpleNamespace(id='secret-'+details.secret_name))
        self.vault.create_secret.side_effect = create_secret
        self.existing_keys = []
        def list_all(method, **kwargs):
            if method == self.ai.list_api_keys:
                return types.SimpleNamespace(data=self.existing_keys)
            if method == self.vault.list_secrets:
                return types.SimpleNamespace(data=[])
            if method == self.compute.list_images:
                return types.SimpleNamespace(data=[types.SimpleNamespace(id='test-image',lifecycle_state='AVAILABLE')])
            raise AssertionError('Unexpected SDK method')
        patches = [
            patch.object(prepare.oci.config,'from_file',return_value={'tenancy':'test-tenant'}),
            patch.object(prepare.oci.generative_ai,'GenerativeAiClient',return_value=self.ai),
            patch.object(prepare.oci.vault,'VaultsClient',return_value=self.vault),
            patch.object(prepare.oci.core,'ComputeClient',return_value=self.compute),
            patch.object(prepare.oci.identity,'IdentityClient',return_value=self.identity),
            patch.object(prepare.oci.pagination,'list_call_get_all_results',side_effect=list_all),
            patch.object(prepare.oci.util,'to_dict',return_value={'id':'test-genai-key','keys':[{'key':'sk-SYNTHETIC-TEST-ONLY'}]}),
            patch('sys.argv',['prepare-runtime.py','--outputs',str(self.outputs),'--checkpoint',str(self.checkpoint),'--variables',str(self.variables)]),
            patch('builtins.print'),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def test_stores_secrets_and_emits_only_references(self):
        prepare.main()
        output = self.variables.read_text()
        self.assertNotIn('sk-SYNTHETIC',output)
        self.assertNotIn('password',output)
        self.assertEqual(len(self.created_secrets),2)
        variables = json.loads(output)
        self.assertEqual(variables['image_ocid'],'test-image')
        self.assertEqual(variables['availability_domain'],'test-ad')

    def test_retry_reuses_checkpoint_without_issuing_more_keys(self):
        prepare.main()
        prepare.main()
        self.ai.create_api_key.assert_called_once()
        self.assertEqual(len(self.created_secrets),2)

    def test_refuses_checkpoint_from_another_tenant(self):
        self.checkpoint.write_text(json.dumps({'scope':{'ai':'another-tenant'}}))
        with self.assertRaises(RuntimeError): prepare.main()
        self.ai.create_api_key.assert_not_called()

    def test_refuses_untracked_existing_key(self):
        self.existing_keys.append(types.SimpleNamespace(display_name='reversa-genai-key'))
        with self.assertRaises(RuntimeError): prepare.main()
        self.ai.create_api_key.assert_not_called()

    def test_cloud_shell_uses_delegated_session_without_user_signing_key(self):
        token = self.root/'delegation'
        token.write_text('SYNTHETIC-DELEGATION-ONLY')
        argv = ['prepare-runtime.py','--outputs',str(self.outputs),'--auth','cloud_shell',
                '--checkpoint',str(self.checkpoint),'--variables',str(self.variables)]
        with patch('sys.argv', argv), \
             patch.dict(os.environ, {'OCI_CLI_CONFIG_FILE':'/etc/oci/config',
                                     'OCI_CLI_PROFILE':'us-chicago-1',
                                     'OCI_CLI_DELEGATION_TOKEN_FILE':str(token)}), \
             patch.object(prepare.oci.auth.signers,'InstancePrincipalsDelegationTokenSigner') as sign:
            prepare.main()
            sign.assert_called_once_with(delegation_token='SYNTHETIC-DELEGATION-ONLY')
        self.assertEqual(len(self.created_secrets),2)


if __name__ == '__main__':
    unittest.main()
