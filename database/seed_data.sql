-- HCBS Seed Data

USE hcbs;

-- CITIES
INSERT INTO cities (city_name) VALUES
('Birmingham'),
('Bristol'),
('Cardiff'),
('London');

-- CINEMAS  (at least 2 per city)
INSERT INTO cinemas (city_id, cinema_name, address, phone) VALUES
(1, 'Horizon Birmingham Central',  '12 Broad Street, Birmingham, B1 2EA',         '0121 000 0001'),
(1, 'Horizon Birmingham Solihull', '45 Mell Square, Solihull, B91 3AX',            '0121 000 0002'),
(2, 'Horizon Bristol Cabot Circus','1 Glass Road, Cabot Circus, Bristol, BS1 3BX', '0117 000 0001'),
(2, 'Horizon Bristol Clifton',     '88 Queens Road, Clifton, Bristol, BS8 1QU',    '0117 000 0002'),
(3, 'Horizon Cardiff Central',     '5 Mary Ann Street, Cardiff, CF10 2EN',         '029 0000 0001'),
(3, 'Horizon Cardiff Bay',         '10 Stuart Street, Cardiff Bay, CF10 5BW',      '029 0000 0002'),
(4, 'Horizon London Leicester Sq', '1 Leicester Square, London, WC2H 7NA',         '020 0000 0001'),
(4, 'Horizon London Canary Wharf', '30 Churchill Place, Canary Wharf, E14 5EU',    '020 0000 0002');

-- SCREENS  (column is total_seats, NOT total_capacity)
-- Lower hall ≈ 30 %, VIP ≤ 10, VIP ⊂ upper gallery
INSERT INTO screens (cinema_id, screen_number, total_seats, lower_hall_seats, upper_gallery_seats, vip_seats) VALUES
-- Horizon Birmingham Central  (cinema_id = 1)
(1, 1, 100, 30, 70, 10),
(1, 2,  80, 24, 56,  5),
(1, 3,  60, 18, 42,  0),
-- Horizon Birmingham Solihull (cinema_id = 2)
(2, 1,  80, 24, 56,  5),
(2, 2,  50, 15, 35,  0),
-- Horizon Bristol Cabot Circus (cinema_id = 3)
(3, 1, 120, 36, 84, 10),
(3, 2, 100, 30, 70,  8),
(3, 3,  80, 24, 56,  5),
(3, 4,  60, 18, 42,  0),
-- Horizon Bristol Clifton (cinema_id = 4)
(4, 1,  80, 24, 56,  5),
(4, 2,  60, 18, 42,  0),
-- Horizon Cardiff Central (cinema_id = 5)
(5, 1, 100, 30, 70, 10),
(5, 2,  80, 24, 56,  5),
(5, 3,  50, 15, 35,  0),
-- Horizon Cardiff Bay (cinema_id = 6)
(6, 1,  80, 24, 56,  5),
(6, 2,  60, 18, 42,  0),
-- Horizon London Leicester Sq (cinema_id = 7)
(7, 1, 120, 36, 84, 10),
(7, 2, 100, 30, 70, 10),
(7, 3, 100, 30, 70,  8),
(7, 4,  80, 24, 56,  5),
(7, 5,  60, 18, 42,  0),
-- Horizon London Canary Wharf (cinema_id = 8)
(8, 1, 120, 36, 84, 10),
(8, 2, 100, 30, 70,  5),
(8, 3,  80, 24, 56,  5);

-- SEATS   (physical seat rows per screen)
-- Naming convention:
--   Lower hall  → L1, L2, …
--   Upper gallery → U1, U2, …
--   VIP         → VIP-1, VIP-2, …
-- We generate seats for every screen using a stored procedure,
-- then drop it afterwards.
DELIMITER $$
CREATE PROCEDURE sp_generate_seats()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_screen_id INT;
    DECLARE v_lower INT;
    DECLARE v_upper INT;
    DECLARE v_vip INT;
    DECLARE v_non_vip_upper INT;
    DECLARE i INT;

    DECLARE cur CURSOR FOR
        SELECT screen_id, lower_hall_seats, upper_gallery_seats, vip_seats
        FROM screens;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_screen_id, v_lower, v_upper, v_vip;
        IF done THEN LEAVE read_loop; END IF;

        -- Lower hall seats
        SET i = 1;
        WHILE i <= v_lower DO
            INSERT INTO seats (screen_id, seat_number, seat_type, row_label)
            VALUES (v_screen_id, CONCAT('L', i), 'lower_hall', CONCAT('L', FLOOR((i - 1) / 10) + 1));
            SET i = i + 1;
        END WHILE;

        -- Upper gallery seats (non-VIP portion)
        SET v_non_vip_upper = v_upper - v_vip;
        SET i = 1;
        WHILE i <= v_non_vip_upper DO
            INSERT INTO seats (screen_id, seat_number, seat_type, row_label)
            VALUES (v_screen_id, CONCAT('U', i), 'upper_gallery', CONCAT('U', FLOOR((i - 1) / 10) + 1));
            SET i = i + 1;
        END WHILE;

        -- VIP seats (subset of upper gallery)
        SET i = 1;
        WHILE i <= v_vip DO
            INSERT INTO seats (screen_id, seat_number, seat_type, row_label)
            VALUES (v_screen_id, CONCAT('VIP-', i), 'vip', 'V');
            SET i = i + 1;
        END WHILE;
    END LOOP;
    CLOSE cur;
END$$
DELIMITER ;

CALL sp_generate_seats();
DROP PROCEDURE sp_generate_seats;

-- ROLES
INSERT INTO roles (role_name) VALUES
('booking_staff'),
('admin'),
('manager');

-- USERS  (username column included — required by schema)
-- password_hash = bcrypt of 'Password123!' for all demo accounts
INSERT INTO users (cinema_id, role_id, username, first_name, last_name, email, password_hash) VALUES
-- Managers (role_id = 3) — one per region
(1, 3, 'jcarter',    'James',  'Carter',   'j.carter@horizoncinemas.co.uk',   '$2b$12$demohashdemohashdemohaLKJ1'),
(3, 3, 'smitchell',  'Sarah',  'Mitchell', 's.mitchell@horizoncinemas.co.uk', '$2b$12$demohashdemohashdemohaLKJ2'),
(5, 3, 'devans',     'David',  'Evans',    'd.evans@horizoncinemas.co.uk',    '$2b$12$demohashdemohashdemohaLKJ3'),
(7, 3, 'psharma',    'Priya',  'Sharma',   'p.sharma@horizoncinemas.co.uk',   '$2b$12$demohashdemohashdemohaLKJ4'),
-- Admins (role_id = 2)
(1, 2, 'ewilson',    'Emma',   'Wilson',   'e.wilson@horizoncinemas.co.uk',   '$2b$12$demohashdemohashdemohaLKJ5'),
(3, 2, 'lbrown',     'Liam',   'Brown',    'l.brown@horizoncinemas.co.uk',    '$2b$12$demohashdemohashdemohaLKJ6'),
(5, 2, 'sthomas',    'Sophie', 'Thomas',   's.thomas@horizoncinemas.co.uk',   '$2b$12$demohashdemohashdemohaLKJ7'),
(7, 2, 'njohnson',   'Noah',   'Johnson',  'n.johnson@horizoncinemas.co.uk',  '$2b$12$demohashdemohashdemohaLKJ8'),
-- Booking staff (role_id = 1)
(1, 1, 'akhan',      'Aisha',  'Khan',     'a.khan@horizoncinemas.co.uk',     '$2b$12$demohashdemohashdemohaLKJ9'),
(1, 1, 'tharris',    'Tom',    'Harris',   't.harris@horizoncinemas.co.uk',   '$2b$12$demohashdemohashdemohaLKJA'),
(3, 1, 'mzhang',     'Mei',    'Zhang',    'm.zhang@horizoncinemas.co.uk',    '$2b$12$demohashdemohashdemohaLKJB'),
(3, 1, 'jroberts',   'Jake',   'Roberts',  'j.roberts@horizoncinemas.co.uk',  '$2b$12$demohashdemohashdemohaLKJC'),
(7, 1, 'cdavies',    'Chloe',  'Davies',   'c.davies@horizoncinemas.co.uk',   '$2b$12$demohashdemohashdemohaLKJD'),
(7, 1, 'omoore',     'Oliver', 'Moore',    'o.moore@horizoncinemas.co.uk',    '$2b$12$demohashdemohashdemohaLKJE');

-- BASE PRICES  (city-level, lower-hall reference price)
INSERT INTO base_prices (city_id, show_period, lower_hall_price) VALUES
(1, 'morning',    5.00),
(1, 'afternoon',  6.00),
(1, 'evening',    7.00),
(2, 'morning',    6.00),
(2, 'afternoon',  7.00),
(2, 'evening',    8.00),
(3, 'morning',    5.00),
(3, 'afternoon',  6.00),
(3, 'evening',    7.00),
(4, 'morning',   10.00),
(4, 'afternoon', 11.00),
(4, 'evening',   12.00);

-- FILMS  (genre must be a single ENUM value; release_date not release_year)
INSERT INTO films (title, description, genre, age_rating, duration_mins, release_date, imdb_rating, cast_list, director) VALUES
('Top Gun: Maverick',
 'After more than thirty years of service as one of the Navy''s top aviators, Maverick pushes the envelope as a courageous test pilot.',
 'Action', 'PG-13', 130, '2022-05-27', 8.5,
 'Tom Cruise, Jennifer Connelly, Miles Teller', 'Joseph Kosinski'),

('Spider-Man: No Way Home',
 'With Spider-Man''s identity now revealed, Peter Parker asks Doctor Strange for help.',
 'Action', 'PG-13', 148, '2021-12-17', 8.3,
 'Tom Holland, Zendaya, Benedict Cumberbatch', 'Jon Watts'),

('The Batman',
 'When a sadistic serial killer begins murdering key political figures in Gotham, Batman is forced to investigate.',
 'Thriller', '15', 176, '2022-03-04', 7.8,
 'Robert Pattinson, Zoë Kravitz, Paul Dano', 'Matt Reeves'),

('Everything Everywhere All at Once',
 'A middle-aged Chinese immigrant is swept up in an adventure where she must connect with parallel universe versions of herself.',
 'Comedy', '15', 139, '2022-03-25', 7.8,
 'Michelle Yeoh, Ke Huy Quan, Jamie Lee Curtis', 'Daniel Kwan, Daniel Scheinert'),

('Oppenheimer',
 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.',
 'Drama', '15', 180, '2023-07-21', 8.9,
 'Cillian Murphy, Emily Blunt, Matt Damon', 'Christopher Nolan'),

('Barbie',
 'Barbie and Ken are having the time of their lives in Barbie Land. When they get a chance to go to the real world, things get complicated.',
 'Comedy', 'PG-13', 114, '2023-07-21', 6.9,
 'Margot Robbie, Ryan Gosling, America Ferrera', 'Greta Gerwig');

-- LISTINGS  (films → screens for a date range)
-- screen_id references: Bristol Cabot = 6,7,8,9  |  London Leic Sq = 17,18
-- created_by must be admin or manager user_id
INSERT INTO listings (film_id, screen_id, start_date, end_date, created_by) VALUES
(1,  6, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 6),   -- Top Gun → Bristol Cabot screen 1
(2,  7, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 6),   -- Spider-Man → Bristol Cabot screen 2
(3,  8, CURDATE(), DATE_ADD(CURDATE(), INTERVAL  7 DAY), 6),   -- The Batman → Bristol Cabot screen 3
(5, 17, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 8),   -- Oppenheimer → London Leic Sq screen 1
(6, 18, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 8);   -- Barbie → London Leic Sq screen 2

-- SHOWINGS  (show_type column is required by schema)
-- morning 08:00-11:59 | afternoon 12:00-16:59 | evening 17:00-23:59
INSERT INTO showings (listing_id, show_time, show_type) VALUES
-- Top Gun: Maverick — 3 shows
(1, '10:00:00', 'morning'),
(1, '14:00:00', 'afternoon'),
(1, '18:00:00', 'evening'),
-- Spider-Man — 3 shows
(2, '10:00:00', 'morning'),
(2, '14:00:00', 'afternoon'),
(2, '18:00:00', 'evening'),
-- The Batman — 2 shows
(3, '12:00:00', 'afternoon'),
(3, '19:30:00', 'evening'),
-- Oppenheimer — 2 shows
(4, '11:00:00', 'morning'),
(4, '17:30:00', 'evening'),
-- Barbie — 3 shows
(5, '10:30:00', 'morning'),
(5, '13:00:00', 'afternoon'),
(5, '16:00:00', 'afternoon');

-- SAMPLE BOOKINGS
-- Bristol evening lower_hall_price = £8.00
-- Upper gallery = £8.00 × 1.20 = £9.60
-- VIP           = £9.60 × 1.20 = £11.52
-- Bristol morning lower = £6.00, upper = £7.20, VIP = £8.64
INSERT INTO bookings (booking_reference, showing_id, show_date, booked_by,
                      customer_name, customer_phone, customer_email,
                      num_tickets, total_cost, booking_status) VALUES
('HC-2025-00001', 3,  DATE_ADD(CURDATE(), INTERVAL 2 DAY), 11,
 'Alice Thompson', '07700900001', 'alice.t@email.com',  2, 16.00, 'confirmed'),
('HC-2025-00002', 6,  DATE_ADD(CURDATE(), INTERVAL 3 DAY), 11,
 'Bob Patel',      '07700900002', 'bob.p@email.com',    3, 28.80, 'confirmed'),
('HC-2025-00003', 1,  DATE_ADD(CURDATE(), INTERVAL 1 DAY),  9,
 'Carol White',    '07700900003', 'carol.w@email.com',  1,  8.64, 'confirmed');

-- BOOKED SEATS  (uses seat_id FK — NOT raw seat_number)
-- We look up seat_id dynamically from the seats table.

-- Booking 1 (Alice): 2 × evening lower hall on screen 6 (Bristol Cabot screen 1)
--   Seats L1, L2 on screen_id 6  →  lower_hall @ £8.00 each
INSERT INTO booked_seats (booking_id, seat_id, unit_price)
SELECT 1, seat_id, 8.00
FROM seats WHERE screen_id = 6 AND seat_number IN ('L1', 'L2');

-- Booking 2 (Bob): 3 × evening upper gallery on screen 7 (Bristol Cabot screen 2)
--   Seats U1, U2, U3 on screen_id 7  →  upper_gallery @ £9.60 each
INSERT INTO booked_seats (booking_id, seat_id, unit_price)
SELECT 2, seat_id, 9.60
FROM seats WHERE screen_id = 7 AND seat_number IN ('U1', 'U2', 'U3');

-- Booking 3 (Carol): 1 × morning VIP on screen 6 (Bristol Cabot screen 1)
--   Seat VIP-1 on screen_id 6  →  vip @ £8.64
INSERT INTO booked_seats (booking_id, seat_id, unit_price)
SELECT 3, seat_id, 8.64
FROM seats WHERE screen_id = 6 AND seat_number = 'VIP-1';