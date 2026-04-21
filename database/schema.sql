-- Horizon Cinemas Booking System (HCBS)
-- Database Schema

DROP DATABASE IF EXISTS hcbs;

CREATE DATABASE IF NOT EXISTS hcbs;
USE hcbs;

-- TABLE: cities
CREATE TABLE cities (
    city_id     INT AUTO_INCREMENT PRIMARY KEY,
    city_name   VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: cinemas
-- Each city has at least 2 cinemas at different locations
CREATE TABLE cinemas (
    cinema_id       INT AUTO_INCREMENT PRIMARY KEY,
    city_id         INT NOT NULL,
    cinema_name     VARCHAR(150) NOT NULL,
    address         VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    total_screens   INT NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cinema_city FOREIGN KEY (city_id) REFERENCES cities(city_id) ON DELETE RESTRICT,
    INDEX idx_city (city_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: screens
-- Each cinema has up to 6 screens
-- Capacity: 50-120 seats total
-- Lower hall: ~30% of total seats
-- Upper gallery: remaining seats (includes VIP subset, max 10)
CREATE TABLE screens (
    screen_id           INT AUTO_INCREMENT PRIMARY KEY,
    cinema_id           INT NOT NULL,
    screen_number       INT NOT NULL,                -- 1-6
    total_seats         INT NOT NULL,                -- 50-120
    lower_hall_seats    INT NOT NULL,                -- ~30% of total
    upper_gallery_seats INT NOT NULL,                -- total - lower_hall_seats
    vip_seats           INT NOT NULL DEFAULT 0,      -- max 10, subset of upper gallery
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_screen_cinema  FOREIGN KEY (cinema_id) REFERENCES cinemas(cinema_id) ON DELETE CASCADE,
    CONSTRAINT uq_screen         UNIQUE (cinema_id, screen_number),
    CONSTRAINT chk_screen_number CHECK (screen_number BETWEEN 1 AND 6),
    CONSTRAINT chk_total_seats   CHECK (total_seats BETWEEN 50 AND 120),
    CONSTRAINT chk_vip_seats     CHECK (vip_seats <= 10),
    INDEX idx_cinema (cinema_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: seats
-- Physical seat records per screen — enables proper conflict detection
-- Prevents double-booking at DB level via booked_seats UNIQUE constraint
CREATE TABLE seats (
    seat_id     INT AUTO_INCREMENT PRIMARY KEY,
    screen_id   INT NOT NULL,
    seat_number VARCHAR(10) NOT NULL,                -- e.g. A1, U12, VIP-3
    seat_type   ENUM('lower_hall', 'upper_gallery', 'vip') NOT NULL,
    row_label   VARCHAR(5) NOT NULL,                 -- e.g. A, B, U1, V
    CONSTRAINT fk_seat_screen FOREIGN KEY (screen_id) REFERENCES screens(screen_id) ON DELETE CASCADE,
    CONSTRAINT uq_seat        UNIQUE (screen_id, seat_number),
    INDEX idx_screen_type (screen_id, seat_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: roles
CREATE TABLE roles (
    role_id     INT AUTO_INCREMENT PRIMARY KEY,
    role_name   ENUM('booking_staff', 'admin', 'manager') NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: users
-- Staff accounts only — system is staff-facing, no customer logins
CREATE TABLE users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    cinema_id       INT NOT NULL,                    -- home cinema of the staff member
    role_id         INT NOT NULL,
    username        VARCHAR(50) NOT NULL UNIQUE,     -- used for login
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,           -- bcrypt hashed
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login      DATETIME,
    CONSTRAINT fk_user_cinema FOREIGN KEY (cinema_id) REFERENCES cinemas(cinema_id) ON DELETE RESTRICT,
    CONSTRAINT fk_user_role   FOREIGN KEY (role_id)   REFERENCES roles(role_id)     ON DELETE RESTRICT,
    INDEX idx_username (username),
    INDEX idx_user_cinema_role (cinema_id, role_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: films
-- Shared film catalogue across all cinemas
CREATE TABLE films (
    film_id         INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    genre           ENUM('Action','Comedy','Drama','Horror','Sci-Fi','Romance','Thriller','Animation','Documentary') NOT NULL,
    age_rating      VARCHAR(10) NOT NULL,            -- PG, PG-13, 15, 18, U etc.
    duration_mins   INT NOT NULL,
    release_date    DATE,                            -- full date
    imdb_rating     DECIMAL(3,1),
    cast_list       TEXT,                            -- comma-separated actor names
    director        VARCHAR(255),
    poster_url      VARCHAR(500),                    -- path/URL for GUI film listing display
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_genre (genre),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: listings
-- Assigns a film to a specific screen for a date range
-- Spec: "film listings may vary from one cinema to another"
-- Created by admins or managers only
CREATE TABLE listings (
    listing_id  INT AUTO_INCREMENT PRIMARY KEY,
    film_id     INT NOT NULL,
    screen_id   INT NOT NULL,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_by  INT NOT NULL,                        -- user_id of admin/manager
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_listing_film    FOREIGN KEY (film_id)    REFERENCES films(film_id)     ON DELETE CASCADE,
    CONSTRAINT fk_listing_screen  FOREIGN KEY (screen_id)  REFERENCES screens(screen_id) ON DELETE CASCADE,
    CONSTRAINT fk_listing_creator FOREIGN KEY (created_by) REFERENCES users(user_id)     ON DELETE RESTRICT,
    CONSTRAINT chk_listing_dates  CHECK (end_date >= start_date),
    INDEX idx_listing_film   (film_id),
    INDEX idx_listing_screen (screen_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: showings
-- Each listing has 1-3 daily show times
-- show_type stored directly (avoids recalculating from show_time each query)
--   morning:   08:00 - 11:59
--   afternoon: 12:00 - 16:59
--   evening:   17:00 - 23:59
CREATE TABLE showings (
    showing_id  INT AUTO_INCREMENT PRIMARY KEY,
    listing_id  INT NOT NULL,
    show_time   TIME NOT NULL,
    show_type   ENUM('morning', 'afternoon', 'evening') NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_showing_listing FOREIGN KEY (listing_id) REFERENCES listings(listing_id) ON DELETE CASCADE,
    INDEX idx_showing_listing (listing_id),
    INDEX idx_showing_date_time (listing_id, show_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: base_prices
-- City-level reference prices (lower hall) per time period
-- All other prices are derived:
--   Upper gallery = lower_hall_price x 1.20
--   VIP           = lower_hall_price x 1.20 x 1.20
CREATE TABLE base_prices (
    price_id         INT AUTO_INCREMENT PRIMARY KEY,
    city_id          INT NOT NULL,
    show_period      ENUM('morning', 'afternoon', 'evening') NOT NULL,
    lower_hall_price DECIMAL(6,2) NOT NULL,
    CONSTRAINT fk_price_city  FOREIGN KEY (city_id) REFERENCES cities(city_id) ON DELETE RESTRICT,
    CONSTRAINT uq_city_period UNIQUE (city_id, show_period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: bookings
-- One booking = one customer transaction for one showing on one date
-- Reference format: HC-YYYY-#####
-- Can be made up to 7 days in advance
-- Cancellation allowed only if show_date > today (not on the day itself)
-- Cancellation charge = 50% of total_cost
CREATE TABLE bookings (
    booking_id          INT AUTO_INCREMENT PRIMARY KEY,
    booking_reference   VARCHAR(20) NOT NULL UNIQUE,
    showing_id          INT NOT NULL,
    show_date           DATE NOT NULL,               -- specific date of this show
    booked_by           INT NOT NULL,                -- staff user_id who processed booking
    customer_name       VARCHAR(255) NOT NULL,
    customer_phone      VARCHAR(20),
    customer_email      VARCHAR(255),
    num_tickets         INT NOT NULL,
    total_cost          DECIMAL(8,2) NOT NULL,
    booking_status      ENUM('confirmed', 'cancelled') NOT NULL DEFAULT 'confirmed',
    payment_simulated   BOOLEAN NOT NULL DEFAULT FALSE,
    booking_date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at        TIMESTAMP NULL,
    cancellation_fee    DECIMAL(8,2) DEFAULT 0.00,   -- 50% of total_cost
    refund_amount       DECIMAL(8,2) DEFAULT 0.00,   -- total_cost - cancellation_fee
    CONSTRAINT fk_booking_showing FOREIGN KEY (showing_id) REFERENCES showings(showing_id) ON DELETE RESTRICT,
    CONSTRAINT fk_booking_staff   FOREIGN KEY (booked_by)  REFERENCES users(user_id)       ON DELETE RESTRICT,
    CONSTRAINT chk_advance_booking CHECK (show_date <= DATE(booking_date) + INTERVAL 7 DAY),
    CONSTRAINT chk_show_date_valid CHECK (show_date >= DATE(booking_date)),
    INDEX idx_reference    (booking_reference),
    INDEX idx_showing      (showing_id),
    INDEX idx_status       (booking_status),
    INDEX idx_show_date    (show_date),
    INDEX idx_booking_date (booking_date),
    INDEX idx_customer     (customer_email, customer_phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: booked_seats
-- Junction table: maps specific seats to a booking
-- Replaces loose seat_number VARCHAR — enables true conflict detection
-- UNIQUE on (booking_id, seat_id) prevents duplicate seats in one booking
CREATE TABLE booked_seats (
    booked_seat_id  INT AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT NOT NULL,
    seat_id         INT NOT NULL,
    unit_price      DECIMAL(6,2) NOT NULL,           -- price paid for this specific seat
    CONSTRAINT fk_bs_booking   FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    CONSTRAINT fk_bs_seat      FOREIGN KEY (seat_id)    REFERENCES seats(seat_id)       ON DELETE RESTRICT,
    CONSTRAINT uq_booking_seat UNIQUE (booking_id, seat_id),
    INDEX idx_booking (booking_id),
    INDEX idx_seat    (seat_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- VIEWS

-- Full showing detail including calculated prices — film listing window
CREATE VIEW v_showing_details AS
SELECT
    sh.showing_id,
    sh.show_time,
    sh.show_type,
    sh.is_active                                         AS showing_active,
    l.listing_id,
    l.start_date,
    l.end_date,
    f.film_id,
    f.title                                              AS film_title,
    f.genre,
    f.age_rating,
    f.duration_mins,
    f.cast_list,
    f.director,
    f.imdb_rating,
    f.poster_url,
    sc.screen_id,
    sc.screen_number,
    sc.total_seats,
    sc.lower_hall_seats,
    sc.upper_gallery_seats,
    sc.vip_seats,
    c.cinema_id,
    c.cinema_name,
    ci.city_id,
    ci.city_name,
    bp.lower_hall_price,
    ROUND(bp.lower_hall_price * 1.20, 2)                 AS upper_gallery_price,
    ROUND(bp.lower_hall_price * 1.20 * 1.20, 2)          AS vip_price
FROM showings sh
JOIN listings l    ON sh.listing_id  = l.listing_id
JOIN films f       ON l.film_id      = f.film_id
JOIN screens sc    ON l.screen_id    = sc.screen_id
JOIN cinemas c     ON sc.cinema_id   = c.cinema_id
JOIN cities ci     ON c.city_id      = ci.city_id
JOIN base_prices bp ON ci.city_id    = bp.city_id AND bp.show_period = sh.show_type
WHERE sh.is_active = TRUE AND l.is_active = TRUE AND f.is_active = TRUE;

-- Seat availability per showing per date — booking window
CREATE VIEW v_seat_availability AS
SELECT
    b.showing_id,
    b.show_date,
    s.seat_type,
    COUNT(bs.booked_seat_id)  AS seats_booked
FROM bookings b
JOIN booked_seats bs ON b.booking_id = bs.booking_id
JOIN seats s         ON bs.seat_id   = s.seat_id
WHERE b.booking_status = 'confirmed'
GROUP BY b.showing_id, b.show_date, s.seat_type;

-- Daily revenue summary — admin reports window
CREATE VIEW v_daily_revenue AS
SELECT
    ci.city_name,
    c.cinema_name,
    DATE(b.booking_date)                                         AS booking_date,
    COUNT(b.booking_id)                                          AS total_bookings,
    SUM(b.total_cost)                                            AS total_revenue,
    SUM(CASE WHEN b.booking_status = 'cancelled' THEN 1 ELSE 0 END) AS cancellations,
    SUM(b.cancellation_fee)                                      AS cancellation_fees_collected
FROM bookings b
JOIN showings sh ON b.showing_id  = sh.showing_id
JOIN listings l  ON sh.listing_id = l.listing_id
JOIN screens sc  ON l.screen_id   = sc.screen_id
JOIN cinemas c   ON sc.cinema_id  = c.cinema_id
JOIN cities ci   ON c.city_id     = ci.city_id
GROUP BY ci.city_name, c.cinema_name, DATE(b.booking_date);

-- Staff booking activity — admin reports (sorted bookings per staff member)
CREATE VIEW v_staff_booking_report AS
SELECT
    u.user_id,
    u.username,
    CONCAT(u.first_name, ' ', u.last_name)   AS staff_name,
    c.cinema_name,
    DATE_FORMAT(b.booking_date, '%Y-%m')     AS month,
    COUNT(b.booking_id)                      AS total_bookings,
    SUM(b.total_cost)                        AS total_revenue_generated
FROM bookings b
JOIN users u   ON b.booked_by = u.user_id
JOIN cinemas c ON u.cinema_id = c.cinema_id
GROUP BY u.user_id, u.username, u.first_name, u.last_name, c.cinema_name,
         DATE_FORMAT(b.booking_date, '%Y-%m')
ORDER BY month DESC, total_bookings DESC;

-- TABLE: ai_chat_sessions
-- Tracks distinct AI chat conversations per user
CREATE TABLE ai_chat_sessions (
    session_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    title       VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_ai_sess_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_sessions (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- TABLE: ai_chat_messages
-- Stores individual messages within a session
CREATE TABLE ai_chat_messages (
    message_id  INT AUTO_INCREMENT PRIMARY KEY,
    session_id  INT NOT NULL,
    role        ENUM('user', 'assistant') NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ai_msg_sess FOREIGN KEY (session_id) REFERENCES ai_chat_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_messages (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

