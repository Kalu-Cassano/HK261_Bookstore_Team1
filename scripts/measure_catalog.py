r"""Reproducible server rendering benchmark on a separate SQLite database.

Run from the project root: .venv\Scripts\python.exe scripts/measure_catalog.py
This does not measure browser rendering, network latency or CDN downloads.
"""
import json
import platform
import sqlite3
import statistics
import sys
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bookstore import create_app  # noqa: E402


def main():
    run = ROOT / '.test-tmp' / ('benchmark-' + uuid4().hex)
    run.mkdir(parents=True)
    app = create_app({'TESTING': True, 'SECRET_KEY': 'benchmark-only-not-for-deployment',
                      'DATABASE': str(run / 'catalog.sqlite3')})
    for command in ('upgrade-db', 'seed-books'):
        result = app.test_cli_runner().invoke(args=[command])
        if result.exit_code:
            raise RuntimeError(result.output)
    samples = []
    client = app.test_client()
    started = perf_counter()
    assert client.get('/books').status_code == 200
    cold_ms = (perf_counter() - started) * 1000
    for _ in range(100):
        started = perf_counter()
        response = client.get('/books')
        samples.append((perf_counter() - started) * 1000)
        assert response.status_code == 200
        assert response.text.count('class="book-cover"') == 12
    report = {'platform': platform.platform(), 'processor': platform.processor(),
              'python': platform.python_version(), 'flask': version('Flask'),
              'sqlite': sqlite3.sqlite_version, 'books': 36, 'requests': 100,
              'method': 'Flask test_client GET /books, anonymous, one process, sequential',
              'cold_ms': round(cold_ms, 3), 'median_ms': round(statistics.median(samples), 3),
              'p95_ms': round(sorted(samples)[94], 3), 'max_ms': round(max(samples), 3),
              'includes_browser_or_network': False}
    print(json.dumps(report, indent=2))
    (run / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
