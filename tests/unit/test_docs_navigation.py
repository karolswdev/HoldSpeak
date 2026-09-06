"""Regression checks for broken or falsely accepted documentation navigation."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_docs.py"
spec = importlib.util.spec_from_file_location("check_docs", SCRIPT)
assert spec and spec.loader
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


class DocumentationNavigationTests(unittest.TestCase):
    def test_heading_formatting_and_duplicate_suffixes(self):
        text = "# A `Thread` (with tools)\n## Again\n## Again\n## Again-1\n## Again\n"
        self.assertEqual(docs.anchors(text), {
            "a-thread-with-tools", "again", "again-1", "again-1-1", "again-2",
        })

    def test_unicode_setext_and_explicit_anchors(self):
        text = '# Café & API\nA second title\n---\n<a id="custom"></a>\n'
        self.assertEqual(docs.anchors(text), {"café--api", "a-second-title", "custom"})

    def test_code_samples_do_not_supply_real_headings_or_links(self):
        text = '# Real\n```md\n# Fake\n[bad](missing.md)\n```\n`[sample](missing.md)`\n'
        self.assertEqual(docs.anchors(text), {"real"})
        self.assertEqual(docs.links(text), [])

    def test_long_fence_is_not_closed_by_short_fence(self):
        text = '````md\n```\n# Fake\n````\n# Real\n'
        self.assertEqual(docs.anchors(text), {"real"})

    def test_links_keep_source_lines_and_reference_definitions(self):
        text = '# Title\n\n[Guide](guide.md#start)\n[ref]: <file name.md#section>\n'
        self.assertEqual(docs.links(text), [(3, "guide.md#start"), (4, "file name.md#section")])

    def test_missing_file_and_anchor_fail_with_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "README.md"
            page.write_text('[a](absent.md)\n[b](guide.md#missing)\n')
            (root / "guide.md").write_text('# Present\n')
            self.assertEqual(docs.check_documents([page], root), [
                'README.md:1: missing target absent.md',
                'README.md:2: missing heading guide.md#missing',
            ])

    def test_same_page_encoded_paths_and_external_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "README.md"
            page.write_text('# Local\n[a](#local)\n[b](a%20file.md#caf%C3%A9)\n'
                            '[web](https://example.test/no-request)\n[app](/settings)\n')
            (root / "a file.md").write_text('# Café\n')
            self.assertEqual(docs.check_documents([page], root), [])

    def test_only_public_markdown_is_in_default_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/internal").mkdir(parents=True)
            (root / "docs/A.md").touch()
            (root / "docs/internal/evidence.md").touch()
            self.assertEqual([p.relative_to(root).as_posix() for p in docs.public_documents(root)],
                             ['README.md', 'CONTRIBUTING.md', 'docs/A.md'])

    def test_missing_document_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(docs.check_documents([root / 'gone.md'], root),
                             ['gone.md: missing document'])


if __name__ == "__main__":
    unittest.main()
