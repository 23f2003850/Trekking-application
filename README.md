# Trekking App

A simple Flask-based trekking management web application where admins, staff, and trekkers can interact with trekking bookings and management features.

## Features

- User registration and login
- Role-based access for:
  - Admin
  - Staff
  - Trekkers
- Admin dashboard for managing treks, users, and staff approval
- Staff dashboard for managing assigned treks and booking status
- Trekkers can view available treks and book them
- Booking history view for users

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite

## Project Structure

- app.py - application entry point
- controllers.py - route definitions and business logic
- models.py - database models
- templates/ - HTML templates for all user roles
- instance/ - local database storage

## Installation

1. Clone the project repository.
2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the Flask app:

```bash
python app.py
```

Then open your browser and go to:

```text
http://127.0.0.1:5000
```

## Default Admin Account

On first run, the app creates a default admin account:

- Email: Founder@trek.com
- Password: Founder123

## Notes

- The app uses a local SQLite database file named trekking.db.
- The database is created automatically when the app starts.

## License

This project is open for educational and personal use.
