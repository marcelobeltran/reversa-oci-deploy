import unittest
import test_results as fixtures


class WorkspaceTests(unittest.TestCase):
    setUp = fixtures.ResultsTests.setUp
    tearDown = fixtures.ResultsTests.tearDown
    get = fixtures.ResultsTests.get

    def make_site(self):
        docs = self.root / '_reversa_docs'
        docs.mkdir()
        (docs / 'index.html').write_text('<!doctype html><h1>Proyecto</h1><a href="pages/">Arquitectura</a>', encoding='utf-8')
        (docs / 'pages').mkdir()
        (docs / 'pages/index.html').write_text('<h1>Arquitectura</h1>', encoding='utf-8')
        (docs / 'style.css').write_text('h1 {color: navy}', encoding='utf-8')
        return docs

    def test_home_links_both_documentation_stages_inside_projects(self):
        response = self.client.get('/')
        self.assertIn(b'?vista=analisis', response.data)
        self.assertIn(b'?vista=html', response.data)
        self.assertNotIn(b'href="/docs/', response.data)

    def test_markdown_is_accessible_before_html_exists(self):
        (self.sdd / 'analysis.md').write_text('# Análisis primero', encoding='utf-8')
        response = self.get('?vista=analisis')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'analysis.md', response.data)
        response = self.get('?vista=html')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'El HTML se genera en una segunda etapa', response.data)
        self.assertIn(b'href="/proyecto/viewer-fixture/?vista=html">Actualizar', response.data)

    def test_both_missing_stages_have_a_usable_view(self):
        self.sdd.rmdir()
        for view in ['analisis', 'html']:
            self.assertEqual(self.get('?vista=' + view).status_code, 200)
        self.assertEqual(self.get('?vista=unexpected').status_code, 404)

    def test_html_is_embedded_inside_project_with_sandbox(self):
        self.make_site()
        response = self.get('?vista=html', headers={'X-Forwarded-Prefix': '/proyectos'})
        self.assertIn(b'<iframe', response.data)
        self.assertIn(b'sandbox=""', response.data)
        self.assertIn(b'src="/proyectos/proyecto/viewer-fixture/sitio/index.html"', response.data)
        self.assertIn(b'frame-src \'self\'', response.headers['Content-Security-Policy'].encode())
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

    def test_html_and_local_styles_are_served_with_restricted_policy(self):
        self.make_site()
        for relative, mime in [('index.html', 'text/html'), ('style.css', 'text/css')]:
            response = self.get('sitio/' + relative)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, mime)
            self.assertIn('sandbox;', response.headers['Content-Security-Policy'])
            self.assertIn("script-src 'none'", response.headers['Content-Security-Policy'])
            self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            response.close()

    def test_html_directory_links_resolve_to_index(self):
        self.make_site()
        response = self.get('sitio/pages')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/sitio/pages/'))
        response = self.get('sitio/pages/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<h1>Arquitectura</h1>', response.data)
        response.close()

    def test_html_asset_route_cannot_expose_other_project_files(self):
        docs = self.make_site()
        (docs / 'private.json').write_text('{"secret": "private"}')
        (docs / 'script.js').write_text('alert(1)')
        (self.sdd / 'analysis.md').write_text('private source')
        for relative in ['../_reversa_sdd/analysis.md', 'private.json', 'script.js', '.config.json', '..%5Csource.html']:
            self.assertEqual(self.get('sitio/' + relative).status_code, 404, relative)

    def test_all_results_keeps_html_source_and_other_outputs_browsable(self):
        self.make_site()
        self.assertIn(b'_reversa_sdd', self.get('?vista=archivos').data)
        self.assertIn(b'index.html', self.get('resultados/_reversa_docs').data)
        response = self.get('resultados/_reversa_docs/index.html')
        self.assertIn(b'<iframe', response.data)
        self.assertIn(b'Ver c', response.data)
