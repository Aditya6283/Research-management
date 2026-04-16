"""
Take a Resource and render it as a reference string in the requested
academic style APA / IEEE / MLA / Chicago (author-date) / Harvard.

The Resource model holds the raw bits (authors, year, venue, volume,
issue, pages, doi). This module is the bit that knows the punctuation
and ordering rules for each style. Real reference managers like Zotero
do the same thing they keep one canonical record per source and
format it differently per style.

There's deliberately no Django dependency in this file. Makes it easy
to test the formatting in isolation.
"""


def _split_authors(raw):
    """Turn 'Smith, J.; Doe, A.' (or 'Smith, J. and Doe, A.') into a list."""
    if not raw:
        return []
    parts = [p.strip() for p in raw.replace(' and ', ';').split(';')]
    return [p for p in parts if p]


def _et_al(authors, threshold=3):
    """Shorten the author list to 'First Author et al' once it gets long.

    No trailing period the caller usually adds its own punctuation,
    and a double period ('et al..') would look broken.
    """
    if not authors:
        return ''
    if len(authors) > threshold:
        return f"{authors[0]} et al"
    if len(authors) == 1:
        return authors[0]
    return ', '.join(authors[:-1]) + ' & ' + authors[-1]
