import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SOURCE = Path(__file__).resolve().parents[1]/'scripts/resource-manager.py'
spec = importlib.util.spec_from_file_location('resource_manager_driver', SOURCE)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class ExistingStackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        token = root/'token'
        token.write_text('synthetic-test-token')
        self.refs = root/'refs.json'
        self.refs.write_text(json.dumps({'tenancy_ocid':'test-tenant','region':'us-chicago-1',
                                        'stack_ocid':'test-stack','plan_job_ocid':'test-plan'}))
        self.config = {'tenancy':'test-tenant','security_token_file':str(token),'key_file':'synthetic-key'}
        self.client = MagicMock()
        self.stack = types.SimpleNamespace(id='test-stack',compartment_id='test-root',
                                          variables={'tenancy_ocid':'test-tenant'})
        self.client.get_stack.return_value = types.SimpleNamespace(data=self.stack,headers={'etag':'test-etag'})
        self.list_results = types.SimpleNamespace(data=[])
        patches = [
            patch.object(driver.oci.config,'from_file',return_value=self.config),
            patch.object(driver.oci.signer,'load_private_key_from_file',return_value=MagicMock()),
            patch.object(driver.oci.auth.signers,'SecurityTokenSigner',return_value=MagicMock()),
            patch.object(driver.oci.resource_manager,'ResourceManagerClient',return_value=self.client),
            patch.object(driver.oci.pagination,'list_call_get_all_results',return_value=self.list_results),
            patch('builtins.print'),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def run_action(self,action):
        with patch('sys.argv',['resource-manager.py',action,'--refs',str(self.refs)]):
            driver.main()

    def test_wrong_session_tenant_never_calls_cloud(self):
        self.config['tenancy'] = 'another-tenant'
        with self.assertRaises(RuntimeError): self.run_action('sync-source')
        self.client.get_stack.assert_not_called()

    def test_wrong_stack_tenant_never_updates(self):
        self.stack.variables['tenancy_ocid'] = 'another-tenant'
        with self.assertRaises(RuntimeError): self.run_action('sync-source')
        self.client.update_stack.assert_not_called()

    def test_active_job_blocks_source_update(self):
        self.list_results.data = [types.SimpleNamespace(lifecycle_state='IN_PROGRESS')]
        with self.assertRaises(RuntimeError): self.run_action('sync-source')
        self.client.update_stack.assert_not_called()

    def test_active_job_blocks_duplicate_plan(self):
        self.list_results.data = [types.SimpleNamespace(lifecycle_state='ACCEPTED')]
        with self.assertRaises(RuntimeError): self.run_action('plan')
        self.client.create_job.assert_not_called()

    def test_apply_refuses_a_plan_from_another_stack(self):
        self.client.get_job.return_value.data = types.SimpleNamespace(
            stack_id='another-stack',operation='PLAN',lifecycle_state='SUCCEEDED')
        with self.assertRaises(RuntimeError): self.run_action('apply')
        self.client.create_job.assert_not_called()


if __name__ == '__main__':
    unittest.main()
