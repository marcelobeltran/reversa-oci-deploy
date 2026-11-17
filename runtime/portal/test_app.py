import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

test_workspace = tempfile.TemporaryDirectory()
root = Path(test_workspace.name)
projects = root / 'projects'
projects.mkdir()
key = root / 'key'
key.write_text('test-secret-only')
os.environ['REVERSA_PROJECTS'] = str(projects)
os.environ['REVERSA_PORTAL_SECRET'] = str(key)
os.environ.pop('REVERSA_INIT_COMMAND', None)
from app import app


def archive(name='repo/main.py', content='print("ok")'):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as output:
        output.writestr(name, content)
    stream.seek(0)
    return stream


class PortalTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        # Test client calls the backend without Caddy's external /proyectos prefix.
        app.config['SESSION_COOKIE_PATH'] = '/'
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session['csrf'] = 'valid-token'

    def post(self, name, data=None, token='valid-token'):
        return self.client.post('/crear', base_url='https://localhost', data={
            'csrf': token, 'name': name,
            'archive': (data or archive(), 'code.zip'),
        }, content_type='multipart/form-data')

    def test_valid_upload_and_duplicate_preserved(self):
        self.assertEqual(self.post('example').status_code, 302)
        self.assertEqual((projects / 'example/main.py').read_text(), 'print("ok")')
        self.post('example', archive(content='changed'))
        self.assertEqual((projects / 'example/main.py').read_text(), 'print("ok")')

    def test_invalid_archive_leaves_no_project(self):
        self.post('invalid', archive('../outside', 'unsafe'))
        self.assertFalse((projects / 'invalid').exists())
        self.assertEqual(list(projects.glob('.upload-*')), [])

    def test_csrf_prevents_upload(self):
        self.post('csrf-rejected', token='wrong')
        self.assertFalse((projects / 'csrf-rejected').exists())

    def test_prefix_and_security_headers(self):
        response = self.client.get('/', base_url='https://localhost', headers={
            'X-Forwarded-Prefix': '/proyectos', 'X-Forwarded-Proto': 'https',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/proyectos/crear', response.data)
        self.assertIn(b'/proyectos/static/style.css', response.data)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')


if __name__ == '__main__':
    unittest.main()
