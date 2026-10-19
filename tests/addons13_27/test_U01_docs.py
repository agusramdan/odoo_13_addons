"""Source-backed documentation checks for U01 (offline/local files only)."""
from support import *
import re
from urllib.parse import unquote, urlsplit

PRD = pathlib.Path('/home/ubuntu/docs/reports/ADDONS13-27/analysis-revision-20261019T062301Z/PRD.md')


class Docs(OfflineCase):
    def test_readme_has_required_navigation_and_exact_local_guides(self):
        readme = (ROOT / 'README.md').read_text()
        self.assertIn('## Untuk Developer', readme)
        self.assertIn('## Untuk User', readme)
        links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', readme)
        self.assertIn('docs/developer.md', links)
        self.assertIn('docs/user.md', links)
        self.assertTrue((ROOT / 'docs/developer.md').is_file())
        self.assertTrue((ROOT / 'docs/user.md').is_file())

    def test_all_local_markdown_links_resolve_without_escaping_candidate(self):
        for doc in (ROOT / 'README.md', ROOT / 'docs/developer.md', ROOT / 'docs/user.md'):
            text = doc.read_text()
            for raw_href in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
                href = raw_href.strip().split('#', 1)[0]
                parsed = urlsplit(href)
                if not href or parsed.scheme or parsed.netloc or href.startswith('mailto:'):
                    continue
                target = (doc.parent / unquote(href)).resolve()
                self.assertTrue(target == ROOT.resolve() or ROOT.resolve() in target.parents,
                                f'link escapes candidate root: {doc.name}: {raw_href}')
                self.assertTrue(target.exists(), f'broken local link: {doc.name}: {raw_href}')

    def test_documented_source_pin_matches_prd_baseline(self):
        prd = PRD.read_text()
        developer = (ROOT / 'docs/developer.md').read_text()
        source_pin = re.search(r'addons_oidc,\s*main\s+([0-9a-f]{40})', prd)
        guide_pin = re.search(r'Pin sumber upstream:\s*`([0-9a-f]{40})`', developer)
        self.assertIsNotNone(source_pin)
        self.assertIsNotNone(guide_pin)
        self.assertEqual(guide_pin.group(1), source_pin.group(1))

    def test_source_line_citations_are_present_and_in_range(self):
        docs = '\n'.join((ROOT / p).read_text() for p in ('docs/developer.md', 'docs/user.md'))
        citations = re.findall(r'(amr_service_client/[A-Za-z0-9_./-]+):(\d+)(?:-(\d+))?', docs)
        self.assertGreaterEqual(len(citations), 50)
        cache = {}
        for relpath, start_text, end_text in citations:
            source = ROOT / relpath
            self.assertTrue(source.is_file(), f'missing cited source: {relpath}')
            lines = cache.setdefault(relpath, source.read_text().splitlines())
            start = int(start_text)
            end = int(end_text or start_text)
            self.assertGreaterEqual(start, 1, relpath)
            self.assertGreaterEqual(end, start, relpath)
            self.assertLessEqual(end, len(lines), f'citation out of range: {relpath}:{start}-{end}')

    def test_guides_separate_source_observation_from_runtime_proof(self):
        text = '\n'.join((ROOT / p).read_text().lower() for p in ('docs/developer.md', 'docs/user.md'))
        self.assertTrue(any(term in text for term in ('belum diverifikasi', 'belum diuji', 'belum dijalankan')))
        self.assertTrue(any(term in text for term in ('not runtime-tested', 'belum ada bukti runtime', 'belum diverifikasi pada runtime', 'tidak membuktikan koneksi')))
