"""
tests/conftest.py
Shared pytest fixtures for both unit and integration tests.

Uses an in-process SQLite database so tests don't need a running MySQL server.
Seeds a minimal but realistic dataset for every test session.
"""

import os
import sys
from datetime import date, time, timedelta

import pytest  # type: ignore
from sqlalchemy import CheckConstraint, create_engine, event, text  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy.schema import DefaultClause  # type: ignore

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override settings BEFORE any app code is imported
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

from backend.core.database import Base, get_db
from backend.core.security import create_access_token, hash_password
from backend.models.booking import BasePrice
from backend.models.cinema import Cinema, City, Screen, Seat
from backend.models.film import Film, Listing, Showing
from backend.models.user import Role, User

# SQLite engine with FK enforcement
TEST_DATABASE_URL = "sqlite:///./test_hcbs.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(test_engine, "connect")
def _set_sqlite_fk_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Database lifecycle
@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session."""
    # SQLite cannot compile some MySQL-specific DDL fragments used by runtime models.
    # Normalize those only for the test metadata before table creation.
    users_table = Base.metadata.tables.get("users")
    if users_table is not None:
        updated_at = users_table.c.get("updated_at")
        if (
            updated_at is not None
            and updated_at.server_default is not None
            and "ON UPDATE" in str(updated_at.server_default.arg).upper()
        ):
            updated_at.server_default = DefaultClause(text("CURRENT_TIMESTAMP"))

    bookings_table = Base.metadata.tables.get("bookings")
    if bookings_table is not None:
        mysql_only_checks = {"chk_advance_booking", "chk_show_date_valid"}
        for constraint in list(bookings_table.constraints):
            if isinstance(constraint, CheckConstraint) and constraint.name in mysql_only_checks:
                bookings_table.constraints.remove(constraint)

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up SQLite file
    test_engine.dispose()
    import pathlib

    db_file = pathlib.Path("test_hcbs.db")
    if db_file.exists():
        try:
            db_file.unlink()
        except PermissionError:
            pass


@pytest.fixture()
def db():
    """Provide a transactional DB session; rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSession(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# Seed data fixture
@pytest.fixture()
def seeded_db(db):
    """
    Seed the test DB with a minimal realistic dataset.
    Returns a dict of key objects for easy reference in tests.

    Dataset:
      - 2 cities: Bristol, London
      - 2 cinemas: Bristol Cabot Circus, London Leicester Sq
      - 1 screen each: 80 seats (24 lower, 56 upper, 5 VIP)
      - Seats generated for each screen
      - 3 roles
      - 3 users: 1 booking_staff, 1 admin, 1 manager
      - Base prices for both cities
      - 1 film: Top Gun
      - 1 listing (14 days from today)
      - 3 showings: morning, afternoon, evening
    """
    # Cities
    bristol = City(city_name="Bristol")
    london = City(city_name="London")
    db.add_all([bristol, london])
    db.flush()

    # Cinemas
    cinema_bristol = Cinema(
        city_id=bristol.city_id,
        cinema_name="Horizon Bristol Cabot Circus",
        address="1 Glass Road, Bristol",
        phone="0117 000 0001",
        total_screens=1,
        is_active=True,
    )
    cinema_london = Cinema(
        city_id=london.city_id,
        cinema_name="Horizon London Leicester Sq",
        address="1 Leicester Square, London",
        phone="020 0000 0001",
        total_screens=1,
        is_active=True,
    )
    db.add_all([cinema_bristol, cinema_london])
    db.flush()

    # Screens
    screen_bristol = Screen(
        cinema_id=cinema_bristol.cinema_id,
        screen_number=1,
        total_seats=80,
        lower_hall_seats=24,
        upper_gallery_seats=56,
        vip_seats=5,
    )
    screen_london = Screen(
        cinema_id=cinema_london.cinema_id,
        screen_number=1,
        total_seats=100,
        lower_hall_seats=30,
        upper_gallery_seats=70,
        vip_seats=10,
    )
    db.add_all([screen_bristol, screen_london])
    db.flush()

    # Generate seats for Bristol screen
    _generate_seats(db, screen_bristol)
    _generate_seats(db, screen_london)

    # Roles
    role_staff = Role(role_name="booking_staff")
    role_admin = Role(role_name="admin")
    role_manager = Role(role_name="manager")
    db.add_all([role_staff, role_admin, role_manager])
    db.flush()

    # Users
    pw = hash_password("Password123!")
    user_staff = User(
        cinema_id=cinema_bristol.cinema_id,
        role_id=role_staff.role_id,
        username="teststaff",
        first_name="Test",
        last_name="Staff",
        email="staff@test.com",
        password_hash=pw,
    )
    user_admin = User(
        cinema_id=cinema_bristol.cinema_id,
        role_id=role_admin.role_id,
        username="testadmin",
        first_name="Test",
        last_name="Admin",
        email="admin@test.com",
        password_hash=pw,
    )
    user_manager = User(
        cinema_id=cinema_london.cinema_id,
        role_id=role_manager.role_id,
        username="testmanager",
        first_name="Test",
        last_name="Manager",
        email="manager@test.com",
        password_hash=pw,
    )
    db.add_all([user_staff, user_admin, user_manager])
    db.flush()

    # Base prices
    for city, prices in [
        (bristol, {"morning": 6.00, "afternoon": 7.00, "evening": 8.00}),
        (london, {"morning": 10.00, "afternoon": 11.00, "evening": 12.00}),
    ]:
        for period, price in prices.items():
            db.add(BasePrice(city_id=city.city_id, show_period=period, lower_hall_price=price))
    db.flush()

    # Film
    film = Film(
        title="Top Gun: Maverick",
        description="Test film",
        genre="Action",
        age_rating="PG-13",
        duration_mins=130,
        release_date=date(2022, 5, 27),
        imdb_rating=8.5,
        cast_list="Tom Cruise",
        director="Joseph Kosinski",
    )
    db.add(film)
    db.flush()

    # Listing (today → 14 days)
    listing = Listing(
        film_id=film.film_id,
        screen_id=screen_bristol.screen_id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=14),
        created_by=user_admin.user_id,
    )
    db.add(listing)
    db.flush()

    # Showings
    showing_morning = Showing(
        listing_id=listing.listing_id,
        show_time=time(10, 0),
        show_type="morning",
    )
    showing_afternoon = Showing(
        listing_id=listing.listing_id,
        show_time=time(14, 0),
        show_type="afternoon",
    )
    showing_evening = Showing(
        listing_id=listing.listing_id,
        show_time=time(18, 0),
        show_type="evening",
    )
    db.add_all([showing_morning, showing_afternoon, showing_evening])
    db.flush()

    db.commit()

    return {
        "cities": {"bristol": bristol, "london": london},
        "cinemas": {"bristol": cinema_bristol, "london": cinema_london},
        "screens": {"bristol": screen_bristol, "london": screen_london},
        "roles": {"staff": role_staff, "admin": role_admin, "manager": role_manager},
        "users": {"staff": user_staff, "admin": user_admin, "manager": user_manager},
        "film": film,
        "listing": listing,
        "showings": {
            "morning": showing_morning,
            "afternoon": showing_afternoon,
            "evening": showing_evening,
        },
    }


# FastAPI test client
@pytest.fixture()
def client(db):
    """FastAPI TestClient with DB dependency overridden to use the test session."""
    from fastapi.testclient import TestClient

    from backend.main import app

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_client(seeded_db, client):
    """TestClient with seeded data already in the DB. Returns (client, seed_data)."""
    return client, seeded_db


# Auth token helpers
@pytest.fixture()
def staff_token(seeded_db):
    u = seeded_db["users"]["staff"]
    return create_access_token(u.user_id, u.username, "booking_staff", u.cinema_id)


@pytest.fixture()
def admin_token(seeded_db):
    u = seeded_db["users"]["admin"]
    return create_access_token(u.user_id, u.username, "admin", u.cinema_id)


@pytest.fixture()
def manager_token(seeded_db):
    u = seeded_db["users"]["manager"]
    return create_access_token(u.user_id, u.username, "manager", u.cinema_id)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# Seat generation helper
def _generate_seats(db, screen: Screen):
    """Mirror the seed data stored procedure — generate seats for a screen."""
    for i in range(1, screen.lower_hall_seats + 1):
        db.add(
            Seat(
                screen_id=screen.screen_id,
                seat_number=f"L{i}",
                seat_type="lower_hall",
                row_label=f"L{(i - 1) // 10 + 1}",
            )
        )
    non_vip = screen.upper_gallery_seats - screen.vip_seats
    for i in range(1, non_vip + 1):
        db.add(
            Seat(
                screen_id=screen.screen_id,
                seat_number=f"U{i}",
                seat_type="upper_gallery",
                row_label=f"U{(i - 1) // 10 + 1}",
            )
        )
    for i in range(1, screen.vip_seats + 1):
        db.add(
            Seat(
                screen_id=screen.screen_id,
                seat_number=f"VIP-{i}",
                seat_type="vip",
                row_label="V",
            )
        )
