import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Set project paths
BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "outputs" / "cleaned"

# Set MySQL connection details
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DATABASE = os.getenv("MYSQL_DATABASE", "asg_airlines")

# Check that the password is available
if not MYSQL_PASSWORD:
    raise ValueError("MYSQL_PASSWORD environment variable is not set.")

# Create MySQL connection
connection_url = URL.create(
    "mysql+pymysql",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=DATABASE
)

engine = create_engine(connection_url)

# Load cleaned CSV files
flights = pd.read_csv(CLEAN_DIR / "flights_clean.csv")
bookings = pd.read_csv(CLEAN_DIR / "bookings_clean.csv")
passengers = pd.read_csv(CLEAN_DIR / "passengers_clean.csv")
payments = pd.read_csv(CLEAN_DIR / "payments_clean.csv")

# Convert flight timestamps
flights["departure_time"] = pd.to_datetime(flights["departure_time"], errors="coerce")
flights["arrival_time"] = pd.to_datetime(flights["arrival_time"], errors="coerce")
flights["duration_minutes"] = pd.to_numeric(flights["duration_minutes"], errors="coerce").astype("Int64")
flights["duration_raw"] = flights["duration_raw"].astype(str)

# Convert booking date
bookings["booking_date"] = pd.to_datetime(bookings["booking_date"], errors="coerce")

# Convert passenger date of birth
passengers["date_of_birth"] = pd.to_datetime(passengers["date_of_birth"], errors="coerce")

# Convert payment amount
payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce")

# Load data into MySQL
flights.to_sql("flights", engine, if_exists="append", index=False)
passengers.to_sql("passengers", engine, if_exists="append", index=False)
bookings.to_sql("bookings", engine, if_exists="append", index=False)
payments.to_sql("payments", engine, if_exists="append", index=False)

# Validate loaded row counts
with engine.connect() as connection:
    for table in ["flights", "passengers", "bookings", "payments"]:
        count = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"{table}: {count} rows")

print("MySQL loading completed successfully.")