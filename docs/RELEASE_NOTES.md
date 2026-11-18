# Release 1.0 — E-Commercial Book Store (Team 1, HK261)

Release date: 19 Nov 2026 · Tag: `v1.0.0` · Base: commit `55167a1` (F1, Sprint 1)

## What is in this release

| Feature | Summary |
|---|---|
| F1 Accounts | Register, log in, log out, account page. Admin and Customer roles. Admin can create, lock and unlock accounts. The last active Admin cannot be locked or downgraded. |
| F2 Book management | Admin adds, edits, hides and shows books. Admin adds, renames and deletes authors and genres; an entry still used by a book cannot be deleted. Server checks title, price (> 0), stock (whole number ≥ 0), author, genre, description and cover URL. All changes use POST with CSRF. |
| F3 Book list | Public list of book cards (cover, title, author, price). 12 books per page, newest first. Hidden books are not shown. Bootstrap grid: 1/2/3/4 columns by screen width. |
| F4 Book details | Details page shows description, genre, stock and ISBN. Unknown or hidden ID shows a friendly 404 page. "Back to books" returns to the same page and filters; it never uses an outside URL. |
| F5 Search and filter | Search by title, author or ISBN (case-insensitive). Filter by genre and price range (AND). Filters stay when the user changes page or opens a book. |
| CR-01 ISBN-13 | Approved by the Sponsor. ISBN is required, 13 digits, unique (also among hidden books). Shown on the details page and searchable. |

## Data

- 52 books: 36 demo books + 16 real titles. Running the seed commands again adds 0 records.
- Prices show in VND, for example `230.000 ₫` and `464.550 ₫`.
- All 52 books use **demo ISBN codes** starting with `000`. The site marks them "Demo code — not a verified edition ISBN". Real ISBNs can be entered by an Admin.
- The database upgrade makes a backup first and keeps all accounts.

## Test result

- `135 passed in 37.60 s` (pytest, 13 Nov 2026, Windows, Python 3.12).
- 19 Nov 2026 (release build, after adding delete for authors/genres): `138 passed in 48.27 s` (pytest, Windows, Python 3.12).
- Manual acceptance and UAT results are in the UAT record (`HK261_SPM_FP_Team1_c5_UAT.docx`).

## Known issues and limits

- No cart, payment or social login (out of scope).
- Demo ISBN codes are not real edition ISBNs.
- Bootstrap and some cover images load from the internet.
- Only server processing time for `/books` was measured (well under 2 s, local test client; see `VALIDATION.md`). Full browser load time is checked in the UAT record.

## How to run

See `README.md`: create `.venv`, install `requirements.txt`, copy `.env.example` to `.env`, then run `upgrade-db`, `seed-books`, `seed-real-books` and `run`.
