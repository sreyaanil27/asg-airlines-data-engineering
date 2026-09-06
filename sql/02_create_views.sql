USE asg_airlines;

# Flight-level analytical view
CREATE OR REPLACE VIEW vw_flight_analysis AS
SELECT
    flight_record_id,
    flight_id,
    airline,
    source,
    destination,
    departure_time,
    arrival_time,
    duration_minutes,
    CASE
        WHEN timestamp_repaired_flag = 1 THEN 'REPAIRED'
        WHEN duration_mismatch_flag = 1 THEN 'DURATION_MISMATCH'
        ELSE 'NORMAL'
    END AS flight_quality_status,
    duplicate_flight_id_flag
FROM flights;

# Route traffic view
CREATE OR REPLACE VIEW vw_route_traffic AS
SELECT
    source,
    destination,
    COUNT(*) AS flight_count,
    COUNT(DISTINCT airline) AS airline_count,
    ROUND(AVG(duration_minutes), 2) AS average_duration_minutes
FROM flights
GROUP BY
    source,
    destination;

# Airline distribution view
CREATE OR REPLACE VIEW vw_airline_distribution AS
SELECT
    airline,
    COUNT(*) AS flight_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM flights),
        2
    ) AS flight_percentage
FROM flights
GROUP BY airline;

# Booking status view
CREATE OR REPLACE VIEW vw_booking_status AS
SELECT
    status,
    COUNT(*) AS booking_count,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM bookings),
        2
    ) AS booking_percentage
FROM bookings
GROUP BY status;

# Payment summary view
CREATE OR REPLACE VIEW vw_payment_summary AS
SELECT
    payment_method,
    COUNT(*) AS payment_count,
    ROUND(SUM(amount), 2) AS total_amount,
    ROUND(AVG(amount), 2) AS average_payment
FROM payments
WHERE amount IS NOT NULL
GROUP BY payment_method;

# Overall KPI view
CREATE OR REPLACE VIEW vw_overall_kpis AS
SELECT
    (SELECT COUNT(*) FROM flights) AS total_flights,
    (SELECT COUNT(*) FROM bookings) AS total_bookings,
    (SELECT COUNT(*) FROM passengers) AS total_passenger_records,
    (SELECT COUNT(*) FROM payments) AS total_payments,
    (SELECT ROUND(AVG(duration_minutes), 2)
     FROM flights
     WHERE duration_minutes IS NOT NULL) AS average_flight_duration_minutes,
    (SELECT COUNT(*)
     FROM flights
     WHERE duration_mismatch_flag = 1
        OR timestamp_repaired_flag = 1) AS flight_anomalies;