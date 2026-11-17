import io
import shutil
import subprocess
import unittest
from unittest.mock import patch

from test_app import app, projects, archive


class ResultsTests(unittest.TestCase):
    def setUp(self):
        self.root = projects / 'viewer-fixture'
        self.root.mkdir()
        self.sdd = self.root / '_reversa_sdd'
        self.sdd.mkdir()
        app.config.update(TESTING=True, SESSION_COOKIE_PATH='/')
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session['csrf'] = 'valid-token'
        self.base = '/proyecto/viewer-fixture/'

    def tearDown(self):
        shutil.rmtree(self.root)

    def get(self, relative='', **kwargs):
        return self.client.get(self.base + relative, base_url='https://localhost', **kwargs)

    def upload(self, data=None, token='valid-token'):
        return self.client.post(self.base + 'cargar', base_url='https://localhost', data={
            'csrf': token, 'archive': (data or archive('extra.txt', 'new input'), 'extra.zip'),
        })

    def test_home_prioritizes_results_and_keeps_create(self):
        response = self.client.get('/')
        self.assertIn(b'Archivos y resultados', response.data)
        self.assertIn(b'action="/crear"', response.data)
        self.assertIn(b'<details class="create-project">', response.data)

    def test_empty_results_then_new_file_visible_without_publishing(self):
        self.assertIn(b'_reversa_sdd', self.get().data)
        self.assertIn(b'archivos de an', self.get('resultados/_reversa_sdd').data)
        (self.sdd / 'analysis.md').write_text('# Análisis\n\n**Contenido**', encoding='utf-8')
        self.assertIn(b'analysis.md', self.get('resultados/_reversa_sdd').data)
        response = self.get('resultados/_reversa_sdd/analysis.md')
        self.assertIn('<h1>Análisis</h1>'.encode(), response.data)
        self.assertIn(b'<strong>Contenido</strong>', response.data)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_markdown_removes_active_html_and_unsafe_urls(self):
        (self.sdd / 'unsafe.md').write_text('<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[click](javascript:alert%281%29)\n\n[sibling](next.md)', encoding='utf-8')
        response = self.get('resultados/_reversa_sdd/unsafe.md')
        self.assertNotIn(b'<script', response.data)
        self.assertNotIn(b'<img', response.data)
        self.assertNotIn(b'href="javascript:', response.data)
        self.assertIn(b'href="next.md"', response.data)

    def test_nested_unicode_paths_and_proxy_prefix(self):
        folder = self.sdd / 'módulo uno'
        folder.mkdir()
        (folder / 'análisis.md').write_text('# Resultado', encoding='utf-8')
        response = self.get('resultados/_reversa_sdd/módulo uno/análisis.md', headers={
            'X-Forwarded-Prefix': '/proyectos', 'X-Forwarded-Proto': 'https',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/proyectos/proyecto/viewer-fixture/descargar/', response.data)
        self.assertIn(b'aria-current="page"', response.data)

    def test_json_and_html_are_escaped_and_download_is_attachment(self):
        (self.sdd / 'index.html').write_text('<script>private()</script>', encoding='utf-8')
        response = self.get('resultados/_reversa_sdd/index.html')
        self.assertIn(b'&lt;script&gt;', response.data)
        self.assertNotIn(b'<script>', response.data)
        (self.sdd / 'modules.json').write_text('{"modules": []}', encoding='utf-8')
        self.assertIn(b'modules', self.get('resultados/_reversa_sdd/modules.json').data)
        response = self.get('descargar/_reversa_sdd/index.html')
        self.assertIn('attachment;', response.headers['Content-Disposition'])
        self.assertEqual(response.mimetype, 'application/octet-stream')
        response.close()

    def test_binary_invalid_utf8_and_large_files_offer_download(self):
        for name, content in [('file.pdf', b'%PDF'), ('bad.txt', b'\xff'), ('nul.txt', b'a\x00b'), ('big.md', b'a' * (2 * 1024 * 1024 + 1))]:
            (self.sdd / name).write_bytes(content)
            response = self.get('resultados/_reversa_sdd/' + name)
            self.assertIn(b'Vista previa no disponible', response.data)
            self.assertIn(b'Descargar archivo', response.data)

    def test_traversal_hidden_sources_and_unknown_project_blocked(self):
        (self.root / 'source.py').write_text('source secret')
        (self.sdd / '.private').write_text('hidden secret')
        for route in ['resultados/source.py', 'resultados/_reversa_sdd/../source.py', 'descargar/_reversa_sdd/../source.py', 'resultados/_reversa_sdd/.private', 'resultados/_reversa_sdd/no-file', 'resultados/_reversa_sdd/..%5Csource.py']:
            self.assertEqual(self.get(route).status_code, 404, route)
        self.assertEqual(self.client.get('/proyecto/missing/').status_code, 404)
        self.assertNotIn(b'.private', self.get('resultados/_reversa_sdd').data)

    def test_symlink_files_and_directories_blocked(self):
        outside = projects / 'viewer-outside'
        outside.mkdir()
        (outside / 'secret.md').write_text('secret')
        try:
            try:
                (self.sdd / 'linked').symlink_to(outside, target_is_directory=True)
                (self.sdd / 'secret.md').symlink_to(outside / 'secret.md')
            except OSError:
                self.skipTest('Creating symlinks requires permission on this host')
            for relative in ['linked/secret.md', 'secret.md']:
                self.assertEqual(self.get('resultados/_reversa_sdd/' + relative).status_code, 404)
                self.assertEqual(self.get('descargar/_reversa_sdd/' + relative).status_code, 404)
            self.assertNotIn(b'linked', self.get('resultados/_reversa_sdd').data)
            docs = self.root / '_reversa_docs'
            docs.mkdir()
            (docs / 'linked').symlink_to(outside, target_is_directory=True)
            (docs / 'index.html').symlink_to(outside / 'secret.md')
            self.assertEqual(self.get('sitio/index.html').status_code, 404)
            self.assertEqual(self.get('sitio/linked/secret.md').status_code, 404)
        finally:
            shutil.rmtree(outside)

    def test_additional_upload_preserves_existing_files(self):
        self.assertEqual(self.upload().status_code, 302)
        self.assertEqual((self.root / 'extra.txt').read_text(), 'new input')
        self.upload(archive('extra.txt', 'replacement'))
        self.assertEqual((self.root / 'extra.txt').read_text(), 'new input')

    def test_additional_upload_csrf_and_traversal(self):
        self.assertEqual(self.upload(token='bad').status_code, 400)
        self.upload(archive('../outside', 'bad'))
        self.assertFalse((self.root / 'extra.txt').exists())
        self.assertEqual(list(projects.glob('.upload-*')), [])

    def test_conflicting_upload_is_atomic(self):
        import zipfile
        (self.root / 'z.txt').write_text('original')
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as output:
            output.writestr('a.txt', 'new')
            output.writestr('z.txt', 'replacement')
        data.seek(0)
        self.upload(data)
        self.assertFalse((self.root / 'a.txt').exists())
        self.assertEqual((self.root / 'z.txt').read_text(), 'original')

    def test_upload_does_not_modify_results(self):
        self.upload(archive('repo/_reversa_sdd/fake.md', 'fake'))
        self.assertFalse((self.sdd / 'fake.md').exists())

    def test_failed_initializer_cleans_new_project(self):
        for failure in [subprocess.CompletedProcess([], 1, '', 'failed'), subprocess.TimeoutExpired('initializer', 120)]:
            with patch.dict('os.environ', {'REVERSA_INIT_COMMAND': '/fixture/initializer'}):
                with patch('app.subprocess.run', **({'side_effect': failure} if isinstance(failure, Exception) else {'return_value': failure})) as run:
                    response = self.client.post('/crear', base_url='https://localhost', data={
                        'csrf': 'valid-token', 'name': 'init-failed-fixture', 'archive': (archive(), 'code.zip'),
                    })
                    self.assertEqual(response.status_code, 302)
                    run.assert_called_once()
                    self.assertFalse((projects / 'init-failed-fixture').exists())


if __name__ == '__main__':
    unittest.main()
