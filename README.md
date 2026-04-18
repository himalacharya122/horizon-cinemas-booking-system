# Horizon Cinemas Booking System (HCBS)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-Desktop_GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Status](https://img.shields.io/badge/Status-CI_Integrated-green?style=for-the-badge)
![UWE Bristol](https://img.shields.io/badge/UWE_Bristol-2024--25-8B0000?style=for-the-badge)

This is a desktop-based cinema booking system built for the Advanced Software Development module at UWE Bristol.

## Overview

HCBS is an internal staff-facing application for Horizon Cinemas — a cinema chain operating across Birmingham, Bristol, Cardiff, and London. The system allows staff to manage film listings, seat bookings, and cancellations across multiple cinema locations.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy
- **Frontend:** PyQt6 (Desktop GUI)
- **Database:** MySQL (Production), SQLite (Testing)
- **Quality Assurance:** Ruff (Linting), Bandit (Security), Pytest (Testing)
- **CI/CD:** GitHub Actions, CircleCI

## User Roles

| Role | Access |
|------|--------|
| Booking Staff | Film listings, bookings, cancellations |
| Admin | All staff access + film/listing management + reports |
| Manager | All admin access + add new cinemas and screens |

## Current System Architecture

```
hcbs/
│
├── config/                      # Environment & database settings
│
├── database/
│   ├── schema.sql               # MySQL schema
│   └── seed_data.sql            # Mock data for testing
│
├── backend/                     # FastAPI application
│   ├── api/v1/endpoints/
│   │   ├── auth.py              # Login, JWT tokens
│   │   ├── bookings.py          # Booking + cancellation
│   │   ├── films.py             # Film listings & showings
│   │   ├── cinemas.py           # Cinema & screen management
│   │   └── users.py             # User management
│   ├── models/                  # SQLAlchemy models (User, Cinema, Film, Booking)
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic (booking, pricing, auth...)
│   └── core/                    # JWT security, custom exceptions
│
├── desktop/                     # PyQt6 GUI application
│   └── ui/windows/
│       ├── login_window.py
│       ├── booking_staff/       # Film listing, booking, cancellation
│       ├── admin/               # Film management, reports
│       └── manager/             # Cinema management
│
├── tests/
│   ├── unit/                    # Model, service, pricing tests
│   └── integration/             # API endpoint & booking flow tests
│
├── .github/workflows/           # GitHub Actions CI pipeline
├── .circleci/                   # CircleCI configuration
└── docs/
    ├── uml/                     # Use case, class & sequence diagrams
    └── agile/                   # Methodology report & contribution log
```

## Getting Started

### Prerequisites
- Python 3.12+
- MySQL Server (for production)
- SQLite (auto-configured for testing)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. Configure environment:
   - Copy `.env.example` to `.env` and fill in your database credentials.

## Running the Application

### 1. Start the Backend API
```bash
python run_server.py
```
The API will be available at `http://localhost:8000`. Documentation: `http://localhost:8000/docs`.

### 2. Start the Desktop GUI
```bash
python run_desktop.py
```

## Development & QA

### Running Tests
We use `pytest` for unit and integration testing. Tests use an in-memory SQLite database and do not require MySQL.
```bash
pytest
```

### Linting & Security
We use **Ruff** for high-performance linting/formatting and **Bandit** for security scanning.
```bash
# Linting & Formatting Check
ruff check .
ruff format --check .

# Security Scan
bandit -r . -x ./venv,./tests -ll
```

### CI/CD Pipelines
The project is configured with automated pipelines that run on every push:
- **GitHub Actions**: Configured in `.github/workflows/ci.yml`.
- **CircleCI**: Configured in `.circleci/config.yml`.

## Project Status
**Active Development** - Core booking system implemented with production-ready CI/CD pipelines.