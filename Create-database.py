# Create-database.py
# Creates or updates salon.db from Appointments.csv.
# The original CSV file is never changed.

import csv
import sqlite3
from pathlib import Path


CSV_FILE_OPTIONS = ["Appointments.csv", "appointments.csv"]
DATABASE_FILE = "salon.db"

REQUIRED_COLUMNS = [
    "appointment_id",
    "date",
    "customer_name",
    "service",
    "stylist",
    "price",
    "status"
]


def find_csv_file():
    """Find the appointment CSV file."""
    for file_name in CSV_FILE_OPTIONS:
        if Path(file_name).exists():
            return file_name
    return None


def clean_text(value):
    """Clean spaces and accidental quote marks from CSV values."""
    return (value or "").strip().strip('"')


def normalise_status(status):
    """Use consistent status names."""
    status = clean_text(status).lower()

    status_map = {
        "completed": "Completed",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
        "no-show": "No-Show",
        "no show": "No-Show",
        "noshow": "No-Show"
    }

    return status_map.get(status, status.title())


def create_tables(cursor):
    """Create the appointments table and helpful search indexes."""

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            appointment_time TEXT,
            customer_name TEXT NOT NULL,
            service TEXT NOT NULL,
            stylist TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointment_date
        ON appointments(date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointment_stylist
        ON appointments(stylist)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointment_status
        ON appointments(status)
    """)


def import_csv_to_database(cursor, csv_file):
    """Import valid appointment records from CSV into SQLite."""

    imported_records = 0
    skipped_records = 0
    skipped_rows = []

    with open(csv_file, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        # Check that the CSV has the required headings
        if reader.fieldnames is None:
            print("ERROR: The CSV file is empty.")
            return imported_records, skipped_records, skipped_rows

        missing_columns = [
            column for column in REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing_columns:
            print("ERROR: Your CSV is missing these columns:")
            print(", ".join(missing_columns))
            return imported_records, skipped_records, skipped_rows

        for row_number, row in enumerate(reader, start=2):
            appointment_id_text = clean_text(row.get("appointment_id"))

            # Skip blank rows or rows containing only quotation marks
            if not appointment_id_text:
                skipped_records += 1
                skipped_rows.append(
                    f"Row {row_number}: empty appointment_id"
                )
                continue

            try:
                appointment_id = int(appointment_id_text)
                price = float(clean_text(row.get("price")).replace(",", ""))

                date = clean_text(row.get("date"))
                appointment_time = clean_text(row.get("appointment_time"))
                customer_name = clean_text(row.get("customer_name"))
                service = clean_text(row.get("service"))
                stylist = clean_text(row.get("stylist"))
                status = normalise_status(row.get("status"))

                # Skip incomplete records
                if not all([
                    date,
                    customer_name,
                    service,
                    stylist,
                    status
                ]):
                    raise ValueError("one or more required fields are empty")

                cursor.execute("""
                    INSERT INTO appointments (
                        appointment_id,
                        date,
                        appointment_time,
                        customer_name,
                        service,
                        stylist,
                        price,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                    ON CONFLICT(appointment_id) DO UPDATE SET
                        date = excluded.date,
                        appointment_time = excluded.appointment_time,
                        customer_name = excluded.customer_name,
                        service = excluded.service,
                        stylist = excluded.stylist,
                        price = excluded.price,
                        status = excluded.status
                """, (
                    appointment_id,
                    date,
                    appointment_time,
                    customer_name,
                    service,
                    stylist,
                    price,
                    status
                ))

                imported_records += 1

            except ValueError as error:
                skipped_records += 1
                skipped_rows.append(f"Row {row_number}: {error}")

    return imported_records, skipped_records, skipped_rows


def show_database_summary(cursor):
    """Display a short summary after importing data."""

    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointment_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(price), 0)
        FROM appointments
        WHERE status = 'Completed'
    """)
    completed_revenue = cursor.fetchone()[0]

    cursor.execute("""
        SELECT service, COUNT(*) AS total
        FROM appointments
        WHERE status = 'Completed'
        GROUP BY service
        ORDER BY total DESC
        LIMIT 1
    """)
    popular_service = cursor.fetchone()

    print("\n" + "=" * 48)
    print("SALON DATABASE CREATED SUCCESSFULLY")
    print("=" * 48)
    print(f"Database file: {DATABASE_FILE}")
    print(f"Appointment records in database: {appointment_count}")
    print(f"Completed appointment revenue: KES {completed_revenue:,.2f}")

    if popular_service:
        print(f"Most popular completed service: {popular_service[0]}")

    print("\nYour original Appointments.csv was not changed.")


def main():
    csv_file = find_csv_file()

    if csv_file is None:
        print("ERROR: Could not find Appointments.csv.")
        print("Save it in the same folder as Create-database.py.")
        return

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    try:
        create_tables(cursor)

        imported, skipped, skipped_rows = import_csv_to_database(
            cursor,
            csv_file
        )

        connection.commit()

        print(f"\nImported or updated records: {imported}")
        print(f"Skipped invalid/blank rows: {skipped}")

        if skipped_rows:
            print("\nSkipped row details:")
            for message in skipped_rows[:10]:
                print(f"- {message}")

        show_database_summary(cursor)

    except sqlite3.Error as error:
        print(f"\nDatabase error: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()