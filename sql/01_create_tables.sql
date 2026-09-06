CREATE DATABASE IF NOT EXISTS asg_airlines;
USE asg_airlines;

DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS passengers;
DROP TABLE IF EXISTS flights;

CREATE TABLE flights (
    flight_record_id INT PRIMARY KEY,
    flight_id VARCHAR(10),
    airline VARCHAR(50),
    airline_raw VARCHAR(50),
    source VARCHAR(10),
    destination VARCHAR(10),
    departure_time DATETIME,
    arrival_time DATETIME,
    duration_minutes INT,
    duration_raw VARCHAR(100),
    airline_derived_flag TINYINT,
    duration_mismatch_flag TINYINT,
    timestamp_repaired_flag TINYINT,
    duplicate_flight_id_flag TINYINT
);

CREATE TABLE passengers (
    passenger_record_id INT PRIMARY KEY,
    passenger_id VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INT,
    age_raw INT,
    gender VARCHAR(10),
    email VARCHAR(255),
    phone VARCHAR(30),
    aadhaar_id VARCHAR(30),
    date_of_birth DATE,
    age_dob_mismatch_flag TINYINT,
    duplicate_passenger_id_flag TINYINT,
    last_name_missing_flag TINYINT
);

CREATE TABLE bookings (
    booking_record_id INT PRIMARY KEY,
    booking_id VARCHAR(20),
    passenger_id VARCHAR(20),
    flight_id VARCHAR(20),
    booking_date DATETIME,
    status VARCHAR(20),
    status_raw VARCHAR(20),
    passport_number VARCHAR(50),
    seat_number VARCHAR(20),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(30),
    status_quality_flag TINYINT
);

CREATE TABLE payments (
    payment_record_id INT PRIMARY KEY,
    payment_id VARCHAR(20),
    booking_id VARCHAR(20),
    amount DECIMAL(12,2),
    amount_raw VARCHAR(100),
    payment_method VARCHAR(30),
    amount_quality_flag TINYINT
);