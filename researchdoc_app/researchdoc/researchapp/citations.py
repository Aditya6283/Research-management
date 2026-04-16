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


def _ieee_authors(authors):
    """IEEE flips the order 'J. Smith' instead of 'Smith, J.'.

    Also caps the visible list at 3 with 'et al.' when there are more
    than 6 authors. APA does that at 21, MLA at 3 every style is
    annoyingly different.
    """
    out = []
    for name in authors:
        if ',' in name:
            surname, initials = [s.strip() for s in name.split(',', 1)]
            out.append(f"{surname} {initials}")
        else:
            out.append(name)
    if len(out) > 6:
        return ', '.join(out[:3]) + ', et al.'
    return ', '.join(out)


def format_citation(resource, style='apa'):
    """Build a citation string for the given Resource in the given style.

    If a field is missing on the resource we just skip it better to
    have an incomplete-but-clean citation than a string full of empty
    "vol. , no. ," fragments.
    """
    authors = _split_authors(getattr(resource, 'authors', ''))
    year = getattr(resource, 'year', '') or 'n.d.'
    title = resource.title
    venue = getattr(resource, 'venue', '')
    volume = getattr(resource, 'volume', '')
    issue = getattr(resource, 'issue', '')
    pages = getattr(resource, 'pages', '')
    doi = getattr(resource, 'doi', '')
    url = getattr(resource, 'url', '')

    style = (style or 'apa').lower()

    if style == 'ieee':
        # [1] J. Smith and A. Doe, "Title," Journal, vol. 1, no. 2, pp. 1-10, 2024.
        parts = []
        if authors:
            parts.append(_ieee_authors(authors) + ',')
        parts.append(f'"{title},"')
        if venue:
            parts.append(f"{venue},")
        if volume:
            parts.append(f"vol. {volume},")
        if issue:
            parts.append(f"no. {issue},")
        if pages:
            parts.append(f"pp. {pages},")
        if year and year != 'n.d.':
            parts.append(f"{year}.")
        if doi:
            parts.append(f"doi: {doi}.")
        return ' '.join(parts)

    if style == 'mla':
        # Smith, John, and Alice Doe. "Title." Journal, vol. 1, no. 2, 2024, pp. 1-10.
        parts = []
        if authors:
            parts.append(_et_al(authors) + '.')
        parts.append(f'"{title}."')
        if venue:
            parts.append(f"{venue},")
        if volume:
            parts.append(f"vol. {volume},")
        if issue:
            parts.append(f"no. {issue},")
        if year and year != 'n.d.':
            parts.append(f"{year},")
        if pages:
            parts.append(f"pp. {pages}.")
        result = ' '.join(parts).rstrip(',')
        if doi:
            result += f" https://doi.org/{doi}."
        return result

    if style == 'chicago':
        # Smith, John, and Alice Doe. 2024. "Title." Journal 1 (2): 1-10.
        parts = []
        if authors:
            parts.append(_et_al(authors) + '.')
        if year and year != 'n.d.':
            parts.append(f"{year}.")
        parts.append(f'"{title}."')
        if venue:
            extra = venue
            if volume:
                extra += f" {volume}"
                if issue:
                    extra += f" ({issue})"
            if pages:
                extra += f": {pages}"
            parts.append(extra + '.')
        if doi:
            parts.append(f"https://doi.org/{doi}.")
        return ' '.join(parts)

    if style == 'harvard':
        # Smith, J. and Doe, A. (2024) 'Title', Journal, 1(2), pp. 1-10.
        parts = []
        if authors:
            parts.append(_et_al(authors))
        parts.append(f"({year})")
        parts.append(f"'{title}',")
        if venue:
            v = venue
            if volume:
                v += f", {volume}"
                if issue:
                    v += f"({issue})"
            parts.append(v + ',')
        if pages:
            parts.append(f"pp. {pages}.")
        result = ' '.join(parts).rstrip(',') + '.'
        if doi:
            result += f" doi: {doi}."
        return result

    # APA 7 default
    # Smith, J., & Doe, A. (2024). Title. Journal, 1(2), 1-10. https://doi.org/...
    parts = []
    if authors:
        if len(authors) > 1:
            parts.append(', '.join(authors[:-1]) + ', & ' + authors[-1])
        else:
            parts.append(authors[0])
    parts.append(f"({year}).")
    parts.append(f"{title}.")
    if venue:
        v = venue
        if volume:
            v += f", {volume}"
            if issue:
                v += f"({issue})"
        if pages:
            v += f", {pages}"
        parts.append(v + '.')
    if doi:
        parts.append(f"https://doi.org/{doi}")
    elif url:
        parts.append(url)
    return ' '.join(parts).strip()


def short_citation(resource):
    authors = _split_authors(getattr(resource, 'authors', ''))
    year = getattr(resource, 'year', '') or 'n.d.'
    if not authors:
        return f"{resource.title} ({year})"
    surnames = []
    for a in authors:
        surnames.append(a.split(',')[0].strip() if ',' in a else a.split()[-1])
    if len(surnames) == 1:
        head = surnames[0]
    elif len(surnames) == 2:
        head = f"{surnames[0]} & {surnames[1]}"
    else:
        head = f"{surnames[0]} et al."
    return f"{head} ({year})"
