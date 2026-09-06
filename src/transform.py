import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, time

# Set project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = BASE_DIR / "data" / "raw" / "UseCase - Airlines.xlsx"
CLEAN_DIR = BASE_DIR / "outputs" / "cleaned"
QUARANTINE_DIR = BASE_DIR / "outputs" / "quarantine"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

# Load raw Excel sheets
flights = pd.read_excel(RAW_FILE, sheet_name="flights")
bookings = pd.read_excel(RAW_FILE, sheet_name="bookings")
passengers = pd.read_excel(RAW_FILE, sheet_name="passengers")
payments = pd.read_excel(RAW_FILE, sheet_name="payments")

# Remove exact duplicate flight records before assigning IDs
flights = flights.drop_duplicates().copy()
flights["flight_record_id"] = range(1, len(flights) + 1)

# Standardize flight timestamps
flights["departure_time"] = pd.to_datetime(flights["departure_time"], errors="coerce")
flights["arrival_time"] = pd.to_datetime(flights["arrival_time"], errors="coerce")
flights["duration_raw"] = flights["duration"].astype(str)

# Convert duration values to minutes
def duration_to_minutes(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, datetime):
        return value.hour * 60 + value.minute + value.second / 60
    if isinstance(value, time):
        return value.hour * 60 + value.minute + value.second / 60
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value) * 24 * 60
    converted = pd.to_timedelta(value, errors="coerce")
    if pd.isna(converted):
        return np.nan
    return converted.total_seconds() / 60

flights["duration_minutes"] = flights["duration"].apply(duration_to_minutes).round().astype("Int64")

# Initialize flight quality flags
flights["timestamp_repaired_flag"] = 0
flights["duration_mismatch_flag"] = 0

# Check flight timestamps against supplied duration
for index, row in flights.iterrows():
    departure = row["departure_time"]
    arrival = row["arrival_time"]
    duration_minutes = row["duration_minutes"]
    if pd.isna(departure) or pd.isna(arrival) or pd.isna(duration_minutes):
        continue
    actual_minutes = (arrival - departure).total_seconds() / 60
    if actual_minutes < 0:
        shifted_arrival = arrival + pd.Timedelta(days=1)
        shifted_minutes = (shifted_arrival - departure).total_seconds() / 60
        if abs(shifted_minutes - duration_minutes) <= 1:
            flights.loc[index, "arrival_time"] = shifted_arrival
            flights.loc[index, "timestamp_repaired_flag"] = 1
        else:
            flights.loc[index, "duration_mismatch_flag"] = 1
    elif abs(actual_minutes - duration_minutes) > 1:
        flights.loc[index, "duration_mismatch_flag"] = 1

# Derive missing airline values from validated flight ID prefixes
flights["airline_raw"] = flights["airline"]
airline_clean = (
    flights["airline"]
    .astype("string")
    .str.strip()
    .replace({"": pd.NA, "UNKNOWN": pd.NA, "unknown": pd.NA})
)
airline_map = {
    "6F": "IndiGo",
    "AI": "Air India",
    "SJ": "SpiceJet",
    "UK": "Vistara"
}
flight_prefix = flights["flight_id"].astype("string").str[:2]
derived_airline = flight_prefix.map(airline_map)
flights["airline_derived_flag"] = (airline_clean.isna() & derived_airline.notna()).astype(int)
flights["airline"] = airline_clean.fillna(derived_airline).fillna("UNKNOWN")

# Flag duplicate flight IDs without removing conflicting records
flight_id_counts = flights["flight_id"].value_counts()
flights["duplicate_flight_id_flag"] = (
    flights["flight_id"].map(flight_id_counts).fillna(0) > 1
).astype(int)

# Keep final flight columns
flights = flights[
    [
        "flight_record_id",
        "flight_id",
        "airline",
        "airline_raw",
        "source",
        "destination",
        "departure_time",
        "arrival_time",
        "duration_minutes",
        "duration_raw",
        "airline_derived_flag",
        "duration_mismatch_flag",
        "timestamp_repaired_flag",
        "duplicate_flight_id_flag"
    ]
]

# Standardize bookings
bookings["booking_record_id"] = range(1, len(bookings) + 1)
bookings["booking_date"] = pd.to_datetime(bookings["booking_date"], errors="coerce")
bookings["status_raw"] = bookings["status"]
bookings["status_quality_flag"] = (
    bookings["status"].isna()
    | bookings["status"].astype("string").str.upper().isin(["INVALID", "UNKNOWN"])
).astype(int)
bookings["status"] = (
    bookings["status"]
    .astype("string")
    .str.strip()
    .str.upper()
    .replace({"": pd.NA, "INVALID": "UNKNOWN"})
    .fillna("UNKNOWN")
)

# Standardize passengers
passengers["passenger_record_id"] = range(1, len(passengers) + 1)
passengers["date_of_birth"] = pd.to_datetime(passengers["date_of_birth"], errors="coerce")
passengers["age_raw"] = pd.to_numeric(passengers["age"], errors="coerce")

# Derive age from date of birth using the reporting date
reporting_date = pd.Timestamp("2026-04-17")

def calculate_age(dob):
    if pd.isna(dob):
        return np.nan
    age = reporting_date.year - dob.year
    if (reporting_date.month, reporting_date.day) < (dob.month, dob.day):
        age -= 1
    return age

passengers["age"] = passengers["date_of_birth"].apply(calculate_age).astype("Int64")

# Flag age and DOB inconsistencies
passengers["age_dob_mismatch_flag"] = (
    passengers["age_raw"].notna()
    & passengers["age"].notna()
    & (passengers["age_raw"] != passengers["age"])
).astype(int)

# Flag duplicate passenger IDs
passenger_id_counts = passengers["passenger_id"].value_counts()
passengers["duplicate_passenger_id_flag"] = (
    passengers["passenger_id"].map(passenger_id_counts).fillna(0) > 1
).astype(int)

# Flag missing last names
passengers["last_name_missing_flag"] = (
    passengers["last_name"].isna()
    | passengers["last_name"].astype("string").str.strip().eq("")
).astype(int)

# Create analytics-safe passenger dataset
passengers_analytics = passengers.copy()

# Mask email addresses
def mask_email(value):
    if pd.isna(value):
        return value
    value = str(value)
    if "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    if not local:
        return "***@" + domain
    return local[0] + "***@" + domain

passengers_analytics["email"] = passengers_analytics["email"].apply(mask_email)

# Mask phone numbers while preserving country code and last four digits
def mask_phone(value):
    if pd.isna(value):
        return value
    digits = "".join(char for char in str(value) if char.isdigit())
    if len(digits) < 6:
        return "***"
    return digits[:2] + "******" + digits[-4:]

passengers_analytics["phone"] = passengers_analytics["phone"].apply(mask_phone)

# Mask Aadhaar numbers while preserving the last four digits
def mask_aadhaar(value):
    if pd.isna(value):
        return value
    digits = "".join(char for char in str(value) if char.isdigit())
    if len(digits) < 4:
        return "****"
    return "*" * (len(digits) - 4) + digits[-4:]

passengers_analytics["aadhaar_id"] = passengers_analytics["aadhaar_id"].apply(mask_aadhaar)

# Save analytics-safe passenger data
passengers_analytics.to_csv(
    CLEAN_DIR / "passengers_analytics.csv",
    index=False
)

# Standardize payments
payments["payment_record_id"] = range(1, len(payments) + 1)
payments["amount_raw"] = payments["amount"].astype(str)
payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce")
payments["amount_quality_flag"] = payments["amount"].isna().astype(int)

# Save cleaned datasets
flights.to_csv(CLEAN_DIR / "flights_clean.csv", index=False)
bookings.to_csv(CLEAN_DIR / "bookings_clean.csv", index=False)
passengers.to_csv(CLEAN_DIR / "passengers_clean.csv", index=False)
payments.to_csv(CLEAN_DIR / "payments_clean.csv", index=False)

# Save quarantine records
flights[
    (flights["duration_mismatch_flag"] == 1)
    | (flights["timestamp_repaired_flag"] == 1)
].to_csv(
    QUARANTINE_DIR / "flight_quality.csv",
    index=False
)

passengers[
    passengers["age_dob_mismatch_flag"] == 1
].to_csv(
    QUARANTINE_DIR / "passenger_age_quality.csv",
    index=False
)

payments[
    payments["amount_quality_flag"] == 1
].to_csv(
    QUARANTINE_DIR / "payment_quality.csv",
    index=False
)

# Print pipeline summary
print("CLEANING PIPELINE COMPLETED")
print(f"Flights cleaned: {len(flights)}")
print(f"Bookings cleaned: {len(bookings)}")
print(f"Passengers cleaned: {len(passengers)}")
print(f"Payments cleaned: {len(payments)}")
print()
print(f"Airline values derived: {flights['airline_derived_flag'].sum()}")
print(f"Flight timestamps repaired: {flights['timestamp_repaired_flag'].sum()}")
print(f"Passenger age/DOB mismatches: {passengers['age_dob_mismatch_flag'].sum()}")
print(f"Invalid payment amounts: {payments['amount_quality_flag'].sum()}")
print("PII-protected passenger dataset created.")
print(f"Output location: {CLEAN_DIR}")