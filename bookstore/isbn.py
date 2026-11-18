"""CR-01 syntax and explicitly synthetic identifiers for unverified editions."""
import re


def valid_isbn(value):
    # CR-01 requires exactly 13 ASCII digits; no edition/checksum claim is made.
    return isinstance(value, str) and re.fullmatch(r'[0-9]{13}', value) is not None


def demo_isbn(used):
    """Return an unused 13-digit demo code, outside real ISBN prefixes."""
    for number in range(1, len(used) + 2):
        candidate = f'000{number:010d}'
        if candidate not in used:
            return candidate
    raise RuntimeError('Could not allocate a demo ISBN.')


def next_demo_isbn(db):
    return demo_isbn({row[0] for row in db.execute('SELECT isbn FROM books')})
