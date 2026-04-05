# Horizon Cinemas Booking System (HCBS)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-Desktop_GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Status](https://img.shields.io/badge/Status-In_Development-orange?style=for-the-badge)
![UWE Bristol](https://img.shields.io/badge/UWE_Bristol-2024--25-8B0000?style=for-the-badge)

This is a desktop-based cinema booking system built for the Advanced Software Development module at UWE Bristol.

## Overview

HCBS is an internal staff-facing application for Horizon Cinemas — a cinema chain operating across Birmingham, Bristol, Cardiff, and London. The system allows staff to manage film listings, seat bookings, and cancellations across multiple cinema locations.

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy
- **Frontend:** PyQt6 (Desktop GUI)
- **Database:** MySQL
- **Auth:** JWT-based authentication

## User Roles

| Role | Access |
|------|--------|
| Booking Staff | Film listings, bookings, cancellations |
| Admin | All staff access + film/listing management + reports |
| Manager | All admin access + add new cinemas and screens |

## Planned System Architecture

> This is the initial planned structure and is subject to change during development.

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
└── docs/
    ├── uml/                     # Use case, class & sequence diagrams
    └── agile/                   # Methodology report & contribution log
```

## Project Status

> Initial setup — development in progress.

## Team

Group project — UWE Bristol.