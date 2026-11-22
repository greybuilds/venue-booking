# Venue Booking System

**An online venue reservation platform for university societies and administrators**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1.3-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)
[![License](https://img.shields.io/badge/License-To%20Be%20Added-lightgrey)](#license)

> **Project status:** Under development. The Django project structure, custom user model, database migration, and application modules currently exist. Booking, society, venue, receipt, and notification features are being developed.

---

## Table of Contents

- [Overview](#overview)
- [Objectives](#objectives)
- [Key Features](#key-features)
- [User Roles](#user-roles)
- [Technology Stack](#technology-stack)
- [Architecture and Project Modules](#architecture-and-project-modules)
- [Database Design](#database-design)
- [OOP Concepts](#oop-concepts)
- [System Requirements](#system-requirements)
- [Local Installation](#local-installation)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Using the Django Admin](#using-the-django-admin)
- [Testing](#testing)
- [Application URLs](#application-urls)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Deployment](#deployment)
- [Production Checklist](#production-checklist)
- [Screenshots](#screenshots)
- [API Documentation](#api-documentation)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [Team and Contributions](#team-and-contributions)
- [License](#license)

---

## Overview

The Venue Booking System is a web-based application designed to simplify the process of booking venues for society events. Society representatives can submit booking requests and view their status, while administrators can manage venues, societies, bookings, receipts, and notifications.

The application uses Django's Model-View-Template (MVT) architecture and is intended to replace manual booking requests, spreadsheets, and untracked approvals.

## Objectives

- Centralize venue and society information.
- Allow society representatives to submit and track booking requests.
- Prevent duplicate or conflicting venue reservations.
- Give administrators visibility and control over all bookings.
- Provide receipts and booking notifications.
- Maintain a traceable booking history.
- Demonstrate object-oriented programming principles in a practical Django project.

## Key Features

> Features below describe the intended system. Confirm a feature is complete before presenting it as implemented.

### Society Representative

- Register and sign in.
- View available venues.
- Submit venue booking requests.
- Select an event date and required time slot.
- Check booking status.
- View approved booking details.
- Receive notifications.
- View or download booking receipts.

### Administrator

- Sign in through the Django admin or a custom dashboard.
- Manage societies and society representatives.
- Add, update, or remove venues.
- Review booking requests.
- Approve or reject bookings.
- View venue availability and schedules.
- Generate or manage receipts.
- Send notifications.

### System Features

- Role-based access using a custom Django user model.
- Centralized SQLite database for local development.
- Django ORM-based database operations.
- Admin interface for model management.
- Environment-based configuration.
- Planned validation for booking conflicts.
- Planned event, booking, and payment audit records.

## User Roles

| Role | Description | Intended permissions |
|---|---|---|
| Society Representative | Member responsible for society activities | Create and view society bookings |
| Administrator | Staff member responsible for approving and managing bookings | Manage societies, venues, bookings, receipts, and notifications |

The custom `User` model is located in [accounts/models.py](accounts/models.py). It extends Django's `AbstractUser` and defines:

- `REP` - Society Representative
- `ADMIN` - Administrator

## Technology Stack

| Area | Technology |
|---|---|
| Programming language | Python 3.12+ |
| Backend framework | Django 6.1.3 |
| Database | SQLite for development |
| Database adapter | psycopg and psycopg-binary |
| Environment variables | python-dotenv |
| Frontend | HTML, CSS, and Django Templates |
| Authentication | Django authentication system |
| Administration | Django Admin |
| Package management | pip |

The exact dependencies are recorded in [requirements.txt](requirements.txt).

## Architecture and Project Modules

The project follows Django's MVT pattern:

```text
Browser
  |
  | HTTP request
  v
URL configuration
  |
  v
View
  |--------------------|
  v                    v
Model / ORM          Template
  |                    |
  v                    v
Database          HTML response
```

### Django Applications

| Application | Responsibility |
|---|---|
| `accounts` | Custom user model and role-based authentication |
| `societies` | Society profiles and society representatives |
| `venues` | Venue details, capacity, location, and availability |
| `bookings` | Booking requests, dates, time slots, and statuses |
| `receipts` | Booking payment and receipt records |
| `notifications` | Notifications for booking updates |
| `config` | Project settings, root URLs, WSGI, and ASGI configuration |

The applications are registered in [config/settings.py](config/settings.py).

## Database Design

The final database should contain relationships similar to the following. These relationships are a planned design and should be updated as models are implemented.

```text
User
  |
  | manages or submits
  v
Society --------< Booking >-------- Venue
                     |
                     | has
                     v
                   Receipt
                     |
                     v
                 Notification
```

### Planned entities

#### User

- Username
- Password
- Email
- Role
- Registration date

#### Society

- Society name
- Description
- Representative
- Creation date

#### Venue

- Venue name
- Location
- Capacity
- Description
- Availability status
- Optional facilities

#### Booking

- Society
- Venue
- Requested date
- Start time
- End time
- Status
- Purpose
- Optional notes
- Creation and update timestamps

#### Receipt

- Booking
- Receipt number
- Amount
- Payment status
- Issue date

#### Notification

- Recipient
- Booking
- Message
- Read status
- Created date

### Booking status example

```text
PENDING -> APPROVED
PENDING -> REJECTED
APPROVED -> CANCELLED
```

The [accounts/migrations](accounts/migrations) directory contains the migration for the custom user model.

## OOP Concepts

This project applies object-oriented programming principles through Django and Python.

### Inheritance

The `User` class inherits from Django's `AbstractUser`:

```python
class User(AbstractUser):
    class Role(models.TextChoices):
        REP = "REP", "Society Rep"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.REP,
    )
```

This reuses Django's complete authentication implementation while extending it with a role field.

### Encapsulation

Models and application behavior are separated into Django apps. Each app manages a distinct concern such as bookings or receipts.

### Abstraction

Django's ORM abstracts SQL operations. Python methods and model fields can be used instead of writing raw SQL for routine database operations.

### Polymorphism

Django supports overriding framework methods and behavior where required, including model methods and view implementations.

### Separation of Concerns

- `models.py` defines data structures.
- `views.py` controls application behavior.
- `urls.py` maps URLs to views.
- Templates control presentation.
- `admin.py` configures Django administration.
- `forms.py` may be used for validated user input.

## System Requirements

Before installing the project, ensure the following are available:

- Windows, macOS, or Linux
- Python 3.12 or newer
- pip
- Git
- A terminal or command prompt
- A modern browser such as Chrome, Edge, Firefox, or Safari

SQLite is included with Python and does not require a separate database server for local development.

## Local Installation

### 1. Clone the repository

```powershell
git clone https://github.com/greybuilds/venue-booking.git
cd venue-booking
```

If cloning is unavailable, download the repository as a ZIP file, extract it, and open a terminal inside the extracted project folder.

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
venv\Scripts\activate.bat
```

macOS or Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Confirm the Django installation

```powershell
python manage.py check
```

## Environment Configuration

The application loads environment variables from `.env` using `python-dotenv`.

Copy the example file:

Windows:

```powershell
Copy-Item .env.example .env
```

macOS or Linux:

```bash
cp .env.example .env
```

Example `.env.example`:

```env
SECRET_KEY=change-me
DEBUG=True
```

Example local `.env`:

```env
SECRET_KEY=replace-this-with-a-long-random-secret-value
DEBUG=True
```

Generate a Django-style secret key with Python:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Do not commit `.env`, real secret keys, database passwords, or deployment credentials.

## Database Setup

Apply the existing migrations:

```powershell
python manage.py migrate
```

Create migration files after changing a model:

```powershell
python manage.py makemigrations
python manage.py migrate
```

For a clean local database, delete `db.sqlite3` only if local data is no longer needed, then run migrations again.

Create an administrator account:

```powershell
python manage.py createsuperuser
```

You will be asked for a username, email, and password.

## Running the Application

Start the Django development server:

```powershell
python manage.py runserver
```

Open:

- Application: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>

The development server is for local testing only. Use a production WSGI server when deploying.

Stop the server with `Ctrl+C`.

## Using the Django Admin

1. Start the server.
2. Open `http://127.0.0.1:8000/admin/`.
3. Sign in with the superuser account.
4. Use the `accounts` and other app entries to view or edit records once models are registered.

For role-specific application pages, implement templates and views rather than exposing all management functionality through the Django admin.

## Testing

Run all tests:

```powershell
python manage.py test
```

Run tests for one application:

```powershell
python manage.py test accounts
python manage.py test societies
python manage.py test venues
python manage.py test bookings
python manage.py test receipts
python manage.py test notifications
```

Check Django configuration:

```powershell
python manage.py check
python manage.py check --deploy
```

The `--deploy` option reports production security settings and may show warnings during local development.

### Recommended test coverage

- User registration and role assignment
- User login and logout
- Administrator access restrictions
- Representative access restrictions
- Society model relationships
- Venue creation and updates
- Booking validation
- Booking conflict prevention
- Booking approval and rejection
- Receipt creation
- Notification creation and read status

## Application URLs

Local URLs:

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/` | Main application |
| `http://127.0.0.1:8000/admin/` | Django administration |

Planned application routes:

| Route | Purpose |
|---|---|
| `/login/` | Sign in |
| `/logout/` | Sign out |
| `/register/` | Society representative registration |
| `/venues/` | Venue listing |
| `/venues/<id>/` | Venue details |
| `/bookings/` | Representative booking list |
| `/bookings/create/` | Create a booking |
| `/bookings/<id>/` | Booking details |
| `/admin/dashboard/` | Administrator dashboard |
| `/admin/bookings/` | Booking management |
| `/notifications/` | Notification list |
| `/receipts/<id>/` | Receipt details |

Update this table after final URLs are implemented.

## Project Structure

```text
venue-booking/
|-- accounts/
|   |-- migrations/
|   |-- admin.py
|   |-- apps.py
|   |-- models.py
|   |-- tests.py
|   `-- views.py
|-- societies/
|-- venues/
|-- bookings/
|-- receipts/
|-- notifications/
|-- config/
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|-- venv/
|-- .env
|-- .env.example
|-- .gitignore
|-- db.sqlite3
|-- manage.py
|-- requirements.txt
`-- README.md
```

The `venv`, `.env`, SQLite database, cache files, and bytecode files should not be committed.

## Development Workflow

### Making model changes

1. Update the appropriate `models.py` file.
2. Run `python manage.py makemigrations`.
3. Review the generated migration.
4. Run `python manage.py migrate`.
5. Add tests.
6. Run `python manage.py test`.
7. Commit the model and migration together.

### Adding a view

1. Define the view or class-based view.
2. Add the route to the relevant app or project URL configuration.
3. Create the template.
4. Restrict access by role or permissions where needed.
5. Test normal, unauthorized, and invalid-input paths.

### Git workflow

```powershell
git status
git pull origin main
git switch -c feature/booking-workflow
# Make changes
git add .
git commit -m "Add booking workflow"
git push origin feature/booking-workflow
```

Replace branch names and commit messages according to the team's convention.

## Deployment

The following is a deployment-ready outline. Replace the dummy values with the selected hosting provider and domain.

### Planned production URL

```text
https://venue-booking.example.com
```

The example URL above is currently a placeholder and does not host the application.

### Dummy hosting examples

```text
Production: https://venue-booking-demo.example.com
Admin:      https://venue-booking-demo.example.com/admin/
Repository: https://github.com/greybuilds/venue-booking
```

Update these values after deployment.

### Before deployment

Complete these changes in [config/settings.py](config/settings.py):

- Set `DEBUG=False`.
- Provide `ALLOWED_HOSTS`.
- Provide `CSRF_TRUSTED_ORIGINS`.
- Use a strong `SECRET_KEY` from the hosting provider's environment variables.
- Configure static files.
- Use persistent PostgreSQL storage for production.
- Use a production WSGI server.
- Configure HTTPS.
- Configure email delivery.
- Configure persistent media storage if receipts or uploaded files are added.
- Run migrations before or during each release.

The current project uses SQLite and is suitable for local development. SQLite is generally not suitable as the shared database for a horizontally scaled production deployment.

### Example environment variables

```env
SECRET_KEY=production-secret-key
DEBUG=False
ALLOWED_HOSTS=venue-booking.example.com
CSRF_TRUSTED_ORIGINS=https://venue-booking.example.com
DATABASE_URL=postgresql://username:password@database-host:5432/venue_booking
```

Never paste real credentials into this README or commit them to Git.

### Example production settings behavior

The project should read deployment values instead of hardcoding them:

```python
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
```

### Example deployment command sequence

Provider-specific commands may differ, but a typical sequence is:

```powershell
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application
```

`gunicorn` is not currently included in [requirements.txt](requirements.txt). Add the production server and deployment dependencies required by the selected provider.

### Static files

Before serving static files in production:

1. Add a static directory structure.
2. Configure `STATIC_ROOT`.
3. Run `python manage.py collectstatic`.
4. Configure the host or reverse proxy to serve the collected files.

### Database migrations during deployment

```powershell
python manage.py migrate
```

Use provider-managed PostgreSQL or another persistent database when possible.

### Deployment platforms

The project can be deployed on platforms such as:

- Railway
- Render
- PythonAnywhere
- an Azure App Service
- an AWS EC2 instance
- a VPS with Nginx and Gunicorn

Use one platform consistently and document the exact provider-specific build and start commands before release.

## Production Checklist

- [ ] Replace `SECRET_KEY=change-me`.
- [ ] Set `DEBUG=False`.
- [ ] Configure `ALLOWED_HOSTS`.
- [ ] Configure `CSRF_TRUSTED_ORIGINS`.
- [ ] Configure PostgreSQL or another production database.
- [ ] Configure HTTPS and redirect HTTP to HTTPS.
- [ ] Configure secure cookies.
- [ ] Configure static files.
- [ ] Configure media storage.
- [ ] Configure email and notification services.
- [ ] Add a production WSGI server.
- [ ] Run `python manage.py migrate`.
- [ ] Run `python manage.py collectstatic --noinput`.
- [ ] Run `python manage.py check --deploy`.
- [ ] Create an administrator account securely.
- [ ] Test login, booking, approval, receipt, and notification flows.
- [ ] Configure backups.
- [ ] Configure application logs and monitoring.
- [ ] Replace all dummy URLs.

## Screenshots

Create a `screenshots` directory and place application images inside it.

```text
screenshots/
|-- login.png
|-- representative-dashboard.png
|-- venue-list.png
|-- booking-form.png
|-- booking-details.png
|-- admin-dashboard.png
`-- receipt.png
```

Then add images in this format:

```markdown
![Login page](screenshots/login.png)
![Administrator dashboard](screenshots/admin-dashboard.png)
```

Screenshots should show the latest working interface and exclude usernames, passwords, personal information, and deployment credentials.

## API Documentation

The project does not currently include a Django REST Framework API configuration.

If an API is added, document:

- API base URL
- Authentication method
- Request formats
- Response formats
- Status codes
- Validation errors
- Example requests
- Protected and public endpoints

Example dummy API URL:

```text
https://api.venue-booking.example.com/v1
```

This URL is a placeholder until an API is implemented and deployed.

## Security

- Never commit `.env`.
- Never commit real secret keys or passwords.
- Store production credentials in hosting environment variables.
- Validate all user input.
- Use Django authentication and permissions.
- Protect booking and receipt routes.
- Prevent unauthorized role access.
- Use HTTPS in production.
- Keep dependencies updated.
- Configure a secure password policy.
- Restrict Django Admin access.
- Prevent SQL injection by using the Django ORM.
- Apply CSRF protection to state-changing forms.
- Review uploaded file types and storage if uploads are added.

## Troubleshooting

### Virtual environment cannot be activated

On PowerShell, set the execution policy for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Alternatively, use Command Prompt:

```bat
venv\Scripts\activate.bat
```

### `SECRET_KEY` error

Confirm that `.env` exists and contains `SECRET_KEY`, then restart the server.

### Database table does not exist

Run:

```powershell
python manage.py migrate
```

### Migration conflict

Review existing migration files and use:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Do not delete migrations when team databases depend on them.

### Package installation error

Confirm that the virtual environment is active and run:

```powershell
python -m pip install -r requirements.txt
```

### Static files are missing

For local development, confirm Django `staticfiles` is installed and the static files are stored in an application static directory.

### Port is already in use

Run Django on another port:

```powershell
python manage.py runserver 8080
```

## Known Limitations

- Most booking, society, venue, receipt, and notification models are not implemented.
- Views and templates are not complete.
- The root URL currently exposes only the Django admin.
- Only the custom account model migration exists.
- Local SQLite is used.
- Production server settings are not yet configured.
- Email delivery is not yet configured for external email providers.
- No API is currently implemented.
- Automated test coverage is minimal.
- Dummy deployment URLs must be replaced.

## Future Improvements

- Complete society and venue CRUD workflows.
- Add venue availability calendars.
- Implement booking conflict detection.
- Add administrator and representative dashboards.
- Add role-based permissions.
- Generate PDF or downloadable receipts.
- Integrate email and SMS notifications.
- Add online payment integration.
- Add audit logs.
- Add REST API endpoints.
- Add PostgreSQL support.
- Add Docker support.
- Add continuous integration and continuous deployment.
- Add automated browser tests.
- Add responsive mobile-friendly layouts.
- Add multi-language support.
- Add recurring or group booking support.

## Team and Contributions

Replace the placeholders below with actual team details.

| Name | Student ID | Role |
|---|---|---|
| Member name | Student ID | Backend and Django models |
| Member name | Student ID | Frontend and templates |
| Member name | Student ID | Testing and documentation |
| Member name | Student ID | Deployment and database |

### Contribution workflow

1. Create or claim an issue.
2. Create a feature branch.
3. Follow the existing Django project structure.
4. Add tests for new behavior.
5. Run Django checks and tests.
6. Open a pull request.
7. Request a code review.
8. Update this README when setup or deployment steps change.

## License

No license has been added yet.

Add one before distributing or making the project public. Suitable choices include an academic-use notice or an open-source license such as MIT, but the team must decide and include the corresponding license file.
