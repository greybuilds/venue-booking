# CONTEXT.md

Paste this at the start of every new AI chat so it uses OUR names and does not invent its own models.

## Project

Venue booking system for university societies. A society rep picks a venue, date and time. The system checks the rules, stops double bookings, and sends a receipt.

## Stack

Django (version in requirements.txt), PostgreSQL (SQLite until week 2), Bootstrap 5, HTMX. Secrets live in .env, read with python-dotenv.

## Apps

accounts, societies, venues, bookings, receipts, notifications

## Models

* User (accounts): extends AbstractUser, role = REP or ADMIN. AUTH\_USER\_MODEL = accounts.User
* Society (societies): president, vice\_president, is\_verified
* Venue (venues): a REAL table, not abstract. Fields: name, building, floor, capacity, opens\_at, closes\_at, requires\_approval, max\_hours, buffer\_minutes
* Classroom(Venue): has\_projector
* Lab(Venue): equipment, supervisor
* SeminarHall(Venue): av\_kit
* Booking (bookings): society, venue, booked\_by, start, end, status
* Receipt (receipts): booking (one to one), reference\_no (unique)
* AuditEntry (notifications): booking, actor, action, old\_status, new\_status, note, time

Multi-table inheritance for venues, so Booking.venue is one ForeignKey to Venue.

## Booking status

PENDING, CONFIRMED, REJECTED, CANCELLED, COMPLETED, EXPIRED
Status never changes by assigning the field. Only through confirm(), reject(reason), cancel(by). Invalid moves raise InvalidTransition.

## Rules (bookings/rules.py)

One class per rule, same shape: validate(booking) returns nothing or raises BookingError("clear reason").
NoClash, OpeningHours, MaxDuration, WeeklyQuota, BlackoutDate

## Ownership

* Member 1: venues models, bookings (models, rules, services), database safety, repo and reviews
* Member 2: accounts, societies
* Member 3: venue screens, calendar, booking form
* Member 4: receipts, notifications, audit log screens, deployment, tests

Do not edit another member's app without telling them.

## Code rules

* Views are thin. Logic lives in models and services (BookingService).
* Datetimes are always timezone aware. Use timezone.now(), never datetime.now(). TIME\_ZONE = Asia/Karachi, USE\_TZ = True.
* Overlap check is strict: s1 < e2 and e1 > s2, so back to back bookings are allowed.
* Permissions are checked on the server, never only hidden in the template.
* Never commit .env, db.sqlite3, venv/ or any key.

## Git

Never push to main. One branch per feature, named feature/what-it-does. Pull main first, commit small, open a PR, the Lead reviews and merges. Tell the chat before running makemigrations in a shared app.