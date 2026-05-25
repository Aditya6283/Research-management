"""
Unit tests for the citation formatter.

These use SimpleTestCase (no database) and a small duck-typed FakeResource
because citations.py is deliberately Django-free — it only reads attributes
off whatever object it's handed. Run with: python manage.py test researchapp
"""
from django.test import SimpleTestCase

from .citations import format_citation, to_bibtex


class FakeResource:
    def __init__(self, **kw):
        defaults = dict(
            resource_type='paper', title='', authors='', year='',
            venue='', volume='', issue='', pages='', doi='', url='',
        )
        defaults.update(kw)
        for key, value in defaults.items():
            setattr(self, key, value)


class CitationFormatTests(SimpleTestCase):
    def test_apa_includes_year_and_title(self):
        r = FakeResource(
            title='Attention Is All You Need',
            authors='Vaswani, A.; Shazeer, N.', year='2017',
            venue='NeurIPS', volume='30', pages='5998-6008',
        )
        out = format_citation(r, 'apa')
        self.assertIn('(2017).', out)
        self.assertIn('Attention Is All You Need', out)

    def test_ieee_puts_initials_before_surname(self):
        r = FakeResource(title='A Study', authors='Vaswani, A.', year='2017')
        self.assertIn('A. Vaswani', format_citation(r, 'ieee'))

    def test_unknown_style_falls_back_to_apa(self):
        r = FakeResource(title='X', authors='Doe, J.', year='2020')
        self.assertEqual(
            format_citation(r, 'totally-not-a-style'),
            format_citation(r, 'apa'),
        )

    def test_missing_year_renders_nd(self):
        r = FakeResource(title='X', authors='Doe, J.')
        self.assertIn('n.d.', format_citation(r, 'apa'))


class BibtexTests(SimpleTestCase):
    def test_paper_becomes_article_entry(self):
        r = FakeResource(
            title='Deep Learning', authors='LeCun, Y.', year='2015',
            venue='Nature', resource_type='paper',
        )
        out = to_bibtex(r)
        self.assertTrue(out.startswith('@article{'))
        self.assertIn('title = {Deep Learning}', out)

    def test_link_becomes_online_entry(self):
        r = FakeResource(
            title='Docs', year='2024', resource_type='link',
            url='https://example.test',
        )
        self.assertTrue(to_bibtex(r).startswith('@online{'))

    def test_empty_fields_are_omitted(self):
        r = FakeResource(title='Bare', resource_type='paper')
        out = to_bibtex(r)
        self.assertNotIn('volume = {}', out)
        self.assertNotIn('doi = {}', out)
