import importlib.util
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cloud_driver', ROOT/'scripts/cloud-shell.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def stack(**variables):
    return types.SimpleNamespace(id='test-stack', compartment_id='test-root', variables={
        'tenancy_ocid': 'test-tenant', 'region': 'us-chicago-1', 'enable_compute': 'false',
        'prefix': 'reversa', **variables})


class CloudShellTests(unittest.TestCase):
    def setUp(self):
        self.config = {'tenancy': 'test-tenant', 'region': 'us-chicago-1'}
        self.rm = MagicMock()

    def test_auth_uses_cloud_shell_environment_and_delegation(self):
        with tempfile.TemporaryDirectory() as temp:
            token = Path(temp)/'delegation'
            token.write_text('SYNTHETIC-DELEGATION-ONLY')
            with patch.dict(os.environ, {'OCI_CLI_CONFIG_FILE': '/etc/oci/config',
                                        'OCI_CLI_PROFILE': 'us-chicago-1'}, clear=True), \
                 patch.object(driver.oci.config, 'from_file', return_value={
                     'tenancy': 'test-tenant', 'delegation_token_file': str(token)}) as read, \
                 patch.object(driver.oci.auth.signers, 'InstancePrincipalsDelegationTokenSigner') as sign:
                config, _ = driver.cloud_auth('us-chicago-1')
                read.assert_called_once_with('/etc/oci/config', 'us-chicago-1')
                sign.assert_called_once_with(delegation_token='SYNTHETIC-DELEGATION-ONLY')
                self.assertEqual(config['region'], 'us-chicago-1')

    def test_wrong_tenant_is_rejected(self):
        with self.assertRaises(RuntimeError):
            driver.check_stack(self.config, stack(tenancy_ocid='other-tenant'))

    def test_wrong_region_is_rejected(self):
        with self.assertRaises(RuntimeError):
            driver.check_stack(self.config, stack(region='other-region'))

    def test_preparation_cannot_disable_a_vm(self):
        for variables, outputs in [({'enable_compute': 'true'}, {}),
                                   ({}, {'instance_ocid': {'value': 'existing-vm'}})]:
            with self.subTest(variables=variables), self.assertRaises(RuntimeError):
                driver.require_no_vm(stack(**variables), outputs)

    def test_active_job_blocks_state_and_mutation(self):
        with patch.object(driver.oci.pagination, 'list_call_get_all_results',
                          return_value=types.SimpleNamespace(data=[types.SimpleNamespace(
                              lifecycle_state='IN_PROGRESS')])):
            with self.assertRaises(RuntimeError):
                driver.job_outputs(self.rm, stack())
        self.rm.get_job_tf_state.assert_not_called()
        self.rm.update_stack.assert_not_called()

    def test_failed_latest_apply_cannot_fall_back_to_old_success(self):
        jobs = [types.SimpleNamespace(operation='APPLY', lifecycle_state=state, time_created=t)
                for t, state in [(1, 'SUCCEEDED'), (2, 'FAILED')]]
        with patch.object(driver.oci.pagination, 'list_call_get_all_results',
                          return_value=types.SimpleNamespace(data=jobs)):
            with self.assertRaises(RuntimeError):
                driver.job_outputs(self.rm, stack())
        self.rm.get_job_tf_state.assert_not_called()

    def test_only_public_references_can_be_synced_and_etag_is_required(self):
        self.rm.get_stack.return_value = types.SimpleNamespace(data=stack(), headers={'etag': 'version-1'})
        with self.assertRaises(RuntimeError):
            driver.sync_references(self.rm, 'test-stack', self.config, {'password': 'synthetic'})
        with patch.object(driver, 'job_outputs', return_value={}):
            driver.sync_references(self.rm, 'test-stack', self.config, {'genai_secret_ocid': 'test-secret'})
        call = self.rm.update_stack.call_args
        self.assertEqual(call.kwargs['if_match'], 'version-1')
        self.assertEqual(call.args[1].variables['enable_compute'], 'false')
        self.rm.create_job.assert_not_called()

    def test_concurrent_vm_enable_blocks_reference_update(self):
        self.rm.get_stack.return_value = types.SimpleNamespace(
            data=stack(enable_compute='true'), headers={'etag': 'changed'})
        with patch.object(driver, 'job_outputs', return_value={}), self.assertRaises(RuntimeError):
            driver.sync_references(self.rm, 'test-stack', self.config, {'genai_secret_ocid': 'test-secret'})
        self.rm.update_stack.assert_not_called()


if __name__ == '__main__':
    unittest.main()
