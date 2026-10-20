# Questionnaires

A web application for creating and passing surveys and tests, built with Django and MySQL.

## Features

- Registration, login by email, logout.
- Two kinds of materials: **surveys** (no right answers) and **tests** (points, correct options, score).
- A material editor on one page: questions and options are added and removed in the browser (JavaScript) and saved with one click in a single transaction. Validation shows all problems at once and keeps the entered data.
- Public and restricted materials. The author grants and revokes access by email on a separate page.
- Passing a material: all questions on one page, several options per question, no time limit and no limit on attempts. Guests can pass public materials.
- Scoring: `score = points * max(0, selected_correct / all_correct - selected_wrong / all_wrong)` for every question; the attempt score is the sum. Surveys have no score.
- Answer review after a test (wrong answers are marked), "My attempts" page.
- Results for the author: summary, per-question statistics, option popularity, list of attempts with details, CSV export (`utf-8-sig`).
- Editing a material that already has attempts: if its structure changes, a confirmation dialog warns that all previous attempts will be deleted.
- Django admin for staff: users (the service user Anonymous is protected), materials (view, search, delete) and read-only questions, options, attempts and answers.
- `seed_demo` command with demo users, materials and attempts.

## Roles

- **Guest**: sees and passes public materials only.
- **User**: sees public materials, own materials and materials shared with them; creates and edits own materials.
- **Admin** (`is_staff`).

## Tech stack

Python 3.13.5, Django 6.1.2, MySQL 8.4 or newer (`mysqlclient`), Django templates, one CSS file and one JavaScript file (no CSS frameworks).

## Project layout

```
config/            Django project (settings, urls)
accounts/          custom User model, registration, login, admin for users
surveys/           materials, editor, attempts, scoring, statistics, export
templates/         base template and icons
schema.sql         creates the database and all tables
requirements.txt   Python dependencies
.env.example       template for database settings
```

All models use `managed = False`: the tables are created by `schema.sql`, and Django migrations do not touch them.

## Requirements

- Python 3.13
- MySQL server 8.4 or newer (Django 6.1 does not support older versions)
- A C compiler and MySQL client headers if `mysqlclient` has to be built from source (Linux: `python3-dev default-libmysqlclient-dev build-essential pkg-config`; macOS: `brew install mysql pkg-config`). On Windows a prebuilt package is normally installed.

## Setup

### 1. Get the code and install dependencies

```bash
git clone <repository-url>
cd <project-folder>
python -m venv .venv
```

Activate the virtual environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Windows cmd: `.venv\Scripts\activate.bat`
- Linux / macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

### 2. Create the database

`schema.sql` creates the database `questionnaires`, all seven tables and the service user Anonymous. Run it with the MySQL client from the project folder.

Linux, macOS, Windows cmd:

```bash
mysql -u root -p < schema.sql
```

Windows PowerShell (the `<` operator is not supported there):

```powershell
mysql -u root -p -e "source schema.sql"
```

If `mysql` is not found, add the `bin` folder of your MySQL installation to `PATH` or use MySQL Workbench (File > Open SQL Script, then Execute).

### 3. Configure the database connection

Copy `.env.example` to `.env` and fill in your values:

```
DB_NAME=questionnaires
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

The `.env` file is ignored by Git, so the password is never committed.

### 4. Apply Django migrations

```bash
python manage.py migrate
```

This creates only Django's own service tables (sessions, admin log, permissions). The application tables from `schema.sql` are not changed.

If you ever recreate the database from `schema.sql` (for example with `DROP DATABASE questionnaires;`), run `python manage.py migrate` again.

### 5. Load demo data (optional)

```bash
python manage.py seed_demo
```

The command is safe to run twice: if demo data already exists it does nothing. To delete the previous demo data and create it again:

```bash
python manage.py seed_demo --reset
```

### 6. Run the server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/. Django admin is at http://127.0.0.1:8000/admin/.

To create your own administrator instead of (or in addition to) the demo one:

```bash
python manage.py createsuperuser
```

## Demo accounts

Created by `seed_demo`:

| Email | Username | Password | Purpose |
|---|---|---|---|
| user1@example.com | user1 | Demo-pass-123 | Test user 1, the author of 5 tests and 5 surveys |
| user2@example.com | user2 | Demo-pass-123 | Test user 2, has access to the restricted materials of user1 |
| user3@example.com | user3 | Demo-pass-123 | Regular user, passed public materials |
| user4@example.com | user4 | Demo-pass-123 | Regular user, passed public materials |
| demo-admin@example.com | demo-admin | Admin-pass-123 | Staff user for Django admin |

Demo data overview:

- user1 authored 10 materials: 3 public tests, 3 public surveys, 2 restricted tests and 2 restricted surveys (restricted ones are available to user1 and user2 only).
- Every material has at least 4 completed attempts with different answers and scores (scores are calculated by the same function as in the application).
- Two public materials ("Retro games quiz", "Weekend plans poll") were created by a user who was deleted afterwards; their author is shown as "Deleted user". Some attempts belong to that deleted user.
- Some attempts were made anonymously (shown as "Anonymous").
- One unfinished attempt exists to show that unfinished attempts are not counted anywhere.

## Notes

- Guests can pass only public materials; restricted materials return 404 for users without access.
- Static files are served by Django's development server. If a newly created static folder returns 404, restart `runserver`.