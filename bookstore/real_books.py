"""Real-title demo catalogue; edition ISBNs unverified, all seed codes marked demo."""
import click
from flask.cli import with_appcontext

from .db import get_db
from .isbn import next_demo_isbn

# Stable keys must survive future corrections to display titles or metadata.
# Prices below are whole VND, converted once on insert to price_cents (VND * 100).
REAL_BOOKS = (
    ('bitcoin-is-for-everyone', 'Bitcoin Is for Everyone', 'Natalie Brunell', 'Cryptocurrency', 464550,
     'A clear introduction to Bitcoin, why it exists, and how it may change the way people think about money.'),
    ('black-box-thinking', 'Black Box Thinking', 'Matthew Syed', 'Personal Development', 664050,
     'Learn how studying mistakes and sharing honest feedback can help people and organizations improve.'),
    ('debt-101', 'Debt 101', 'Michele Cagan', 'Personal Finance', 350550,
     'An accessible guide to borrowing, credit, interest, and practical ways to manage personal debt.'),
    ('debt-free-forever', 'Debt-Free Forever', 'Gail Vaz-Oxlade', 'Personal Finance', 208050,
     'Practical steps for building a budget, paying down debt, and developing healthier money habits.'),
    ('economics-the-economist-guide', 'Economics: The Economist Guide', 'Philip Coggan', 'Economics', 379050,
     'An approachable guide to economic ideas and how they help explain markets, policy, and everyday decisions.'),
    ('extreme-economies', 'Extreme Economies', 'Richard Davies', 'Economics', 303050,
     'Stories from unusual economies show how people adapt to difficult conditions and changing economic forces.'),
    ('financial-services-revolution', 'Financial Services Revolution', 'Alex Tapscott (editor)', 'Finance & Technology', 531050,
     'A collection of perspectives on how blockchain technology could reshape financial services and institutions.'),
    ('how-i-invest-my-money', 'How I Invest My Money', 'Joshua Brown and Brian Portnoy (editors)', 'Investing', 512050,
     'Investors share how they manage their own money and how personal values shape their financial choices.'),
    ('how-to-make-the-world-add-up', 'How to Make the World Add Up', 'Tim Harford', 'Statistics', 331550,
     'A friendly guide to questioning numbers, understanding statistics, and making sense of claims in the news.'),
    ('just-keep-buying', 'Just Keep Buying', 'Nick Maggiulli', 'Investing', 426550,
     'A data-informed look at saving and investing, with practical ideas for building wealth over time.'),
    ('a-more-beautiful-question', 'A More Beautiful Question', 'Warren Berger', 'Personal Development', 436050,
     'Explore how asking thoughtful questions can unlock new ideas, solve problems, and inspire meaningful change.'),
    ('no-bullshit-leadership', 'No Bullsh*t Leadership', 'Chris Hirst', 'Leadership', 350550,
     'Straightforward lessons on leading teams, making decisions, and turning plans into action.'),
    ('no-worries', 'No Worries', 'Jared Dillian', 'Personal Finance', 426550,
     'A practical discussion of money decisions and habits that can help reduce financial stress.'),
    ('number-go-up', 'Number Go Up', 'Zeke Faux', 'Cryptocurrency', 350550,
     'A reported journey through the cryptocurrency boom, exploring its promises, personalities, and risks.'),
    ('play-nice', 'Play Nice', 'Jason Schreier', 'Business & Technology', 474050,
     'The story of Blizzard Entertainment, its games, and the business and workplace struggles behind its success.'),
    ('real-estate-investing-101', 'Real Estate Investing 101', 'Michele Cagan', 'Real Estate', 350550,
     'An introductory guide to property investing, including financing, rental income, expenses, and common risks.'),
)


def metadata_id(db, table, name):
    """Reuse matching metadata without changing its spelling or linked records."""
    # table is supplied only by the two internal constant callers below.
    row = db.execute(f'SELECT id FROM {table} WHERE casefold(trim(name))=casefold(?) ORDER BY id LIMIT 1', (name,)).fetchone()
    if row:
        return row['id']
    return db.execute(f'INSERT INTO {table}(name) VALUES(?)', (name,)).lastrowid


@click.command('seed-real-books')
@with_appcontext
def seed_real_books_command():
    """Add 16 real titles once, preserving all existing books and accounts."""
    db = get_db()
    count = 0
    try:
        db.execute('BEGIN IMMEDIATE')
        for slug, title, author, genre, price_vnd, description in REAL_BOOKS:
            key = 'real-books-v1-' + slug
            # Key catches previously seeded books even after Admin edits a title/author.
            # Title + author also catches books already entered manually, without tagging
            # or otherwise modifying those existing rows.
            existing = db.execute('''SELECT b.id FROM books b JOIN authors a ON a.id=b.author_id
                WHERE b.demo_key=? OR
                (casefold(trim(b.title))=casefold(?) AND casefold(trim(a.name))=casefold(?))
                LIMIT 1''', (key, title, author)).fetchone()
            if existing:
                continue
            aid = metadata_id(db, 'authors', author)
            gid = metadata_id(db, 'genres', genre)
            # No matching individual covers are bundled. Empty uses the local cover.svg.
            db.execute('''INSERT INTO books(title,author_id,genre_id,price_cents,description,cover_url,stock,demo_key,isbn,isbn_is_demo)
                VALUES(?,?,?,?,?,?,?,?,?,1)''', (title, aid, gid, price_vnd * 100, description, '', 10, key, next_demo_isbn(db)))
            count += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    total = db.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    click.echo(f'Inserted {count} real books. Total books: {total}. Existing data was kept.')
