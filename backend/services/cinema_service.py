# ============================================
# Author: Astha Gurung
# Student ID: 24036542
# Last Edited: 2026-04-25
# ============================================

"""
backend/services/cinema_service.py
Business logic for cities, cinemas, screens, seats, and base prices.
Manager-level operations: add new cinemas in existing or new cities.
"""

from sqlalchemy.orm import Session, joinedload  # type: ignore

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.booking import BasePrice
from backend.models.cinema import Cinema, City, Screen, Seat


# Cities
def get_all_cities(db: Session) -> list[City]:
    return db.query(City).order_by(City.city_name).all()


def get_city(db: Session, city_id: int) -> City:
    city = db.query(City).filter(City.city_id == city_id).first()
    if not city:
        raise NotFoundError("City")
    return city


def create_city(db: Session, city_name: str) -> City:
    existing = db.query(City).filter(City.city_name == city_name).first()
    if existing:
        raise ValidationError(f"City '{city_name}' already exists")
    city = City(city_name=city_name)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


# Cinemas
def get_all_cinemas(
    db: Session, city_id: int | None = None, active_only: bool = True
) -> list[Cinema]:
    query = db.query(Cinema).options(
        joinedload(Cinema.city),
        joinedload(Cinema.screens),
    )
    if city_id:
        query = query.filter(Cinema.city_id == city_id)
    if active_only:
        query = query.filter(Cinema.is_active == True)  # noqa: E712
    return query.order_by(Cinema.cinema_name).all()


def get_cinema(db: Session, cinema_id: int) -> Cinema:
    cinema = (
        db.query(Cinema)
        .options(joinedload(Cinema.city), joinedload(Cinema.screens))
        .filter(Cinema.cinema_id == cinema_id)
        .first()
    )
    if not cinema:
        raise NotFoundError("Cinema")
    return cinema


def create_cinema(db: Session, data: dict) -> Cinema:
    """
    Create a new cinema (Manager only).
    Can reference an existing city_id or create a new city via new_city_name.
    Optionally creates screens + generates seats.
    """
    city_id = data.get("city_id")
    new_city_name = data.get("new_city_name")

    if not city_id and not new_city_name:
        raise ValidationError("Provide either city_id or new_city_name")

    if new_city_name:
        city = create_city(db, new_city_name)
        city_id = city.city_id
    else:
        # Verify city exists
        get_city(db, city_id)

    cinema = Cinema(
        city_id=city_id,
        cinema_name=data["cinema_name"],
        address=data["address"],
        phone=data.get("phone"),
        total_screens=len(data.get("screens", [])),
    )
    db.add(cinema)
    db.flush()

    # Create screens and seats
    for screen_data in data.get("screens", []):
        _create_screen_with_seats(db, cinema.cinema_id, screen_data)

    db.commit()
    db.refresh(cinema)
    return cinema


def update_cinema(db: Session, cinema_id: int, data: dict) -> Cinema:
    cinema = get_cinema(db, cinema_id)
    for key, value in data.items():
        if value is not None:
            setattr(cinema, key, value)
    db.commit()
    db.refresh(cinema)
    return cinema


# Screens
def add_screen_to_cinema(db: Session, cinema_id: int, data: dict) -> Screen:
    """Add a new screen to an existing cinema and generate its seats."""
    cinema = get_cinema(db, cinema_id)

    # Check max 6 screens
    active_screens = [s for s in cinema.screens if s.is_active]
    if len(active_screens) >= 6:
        raise ValidationError("A cinema can have a maximum of 6 screens")

    # Check screen number not duplicate
    existing_numbers = {s.screen_number for s in cinema.screens}
    if data["screen_number"] in existing_numbers:
        raise ValidationError(f"Screen {data['screen_number']} already exists at this cinema")

    screen = _create_screen_with_seats(db, cinema_id, data)
    cinema.total_screens = len([s for s in cinema.screens if s.is_active]) + 1
    db.commit()
    db.refresh(screen)
    return screen


def _create_screen_with_seats(db: Session, cinema_id: int, data: dict) -> Screen:
    """Create a screen and auto-generate its seat records."""
    total = data["total_seats"]
    lower = data["lower_hall_seats"]
    upper = data["upper_gallery_seats"]
    vip = data.get("vip_seats", 0)

    # Validate seat arithmetic
    if lower + upper != total:
        raise ValidationError("lower_hall_seats + upper_gallery_seats must equal total_seats")
    if vip > upper:
        raise ValidationError("VIP seats cannot exceed upper gallery seats")

    screen = Screen(
        cinema_id=cinema_id,
        screen_number=data["screen_number"],
        total_seats=total,
        lower_hall_seats=lower,
        upper_gallery_seats=upper,
        vip_seats=vip,
    )
    db.add(screen)
    db.flush()

    # Generate seat records
    _generate_seats(db, screen)
    return screen


def _generate_seats(db: Session, screen: Screen):
    """Generate physical seat records for a screen."""
    # Lower hall seats
    for i in range(1, screen.lower_hall_seats + 1):
        seat = Seat(
            screen_id=screen.screen_id,
            seat_number=f"L{i}",
            seat_type="lower_hall",
            row_label=f"L{(i - 1) // 10 + 1}",
        )
        db.add(seat)

    # Upper gallery seats (non-VIP)
    non_vip_upper = screen.upper_gallery_seats - screen.vip_seats
    for i in range(1, non_vip_upper + 1):
        seat = Seat(
            screen_id=screen.screen_id,
            seat_number=f"U{i}",
            seat_type="upper_gallery",
            row_label=f"U{(i - 1) // 10 + 1}",
        )
        db.add(seat)

    # VIP seats
    for i in range(1, screen.vip_seats + 1):
        seat = Seat(
            screen_id=screen.screen_id,
            seat_number=f"VIP-{i}",
            seat_type="vip",
            row_label="V",
        )
        db.add(seat)


# Base prices
def get_base_prices(db: Session, city_id: int | None = None) -> list[BasePrice]:
    query = db.query(BasePrice)
    if city_id:
        query = query.filter(BasePrice.city_id == city_id)
    return query.order_by(BasePrice.city_id, BasePrice.show_period).all()


def set_base_price(db: Session, city_id: int, show_period: str, price: float) -> BasePrice:
    """Create or update a base price for a city + period."""
    get_city(db, city_id)  # validate city exists

    bp = (
        db.query(BasePrice)
        .filter(BasePrice.city_id == city_id, BasePrice.show_period == show_period)
        .first()
    )

    if bp:
        bp.lower_hall_price = price
    else:
        bp = BasePrice(city_id=city_id, show_period=show_period, lower_hall_price=price)
        db.add(bp)

    db.commit()
    db.refresh(bp)
    return bp
