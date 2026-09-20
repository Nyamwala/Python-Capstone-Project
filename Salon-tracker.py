# salon_tracker.py
# Salon Appointment Tracker and Business Insights Project

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# SETTINGS
# -----------------------------
DATA_FILE = "appointments.csv"
OUTPUT_FOLDER = "outputs"


# -----------------------------
# LOAD AND CLEAN DATA
# -----------------------------
def load_data(file_name):
    """Load salon appointment data from a CSV file."""

    try:
        df = pd.read_csv(file_name)
    except FileNotFoundError:
        print(f"\nERROR: Cannot find '{file_name}'.")
        print("Make sure appointments.csv is in the same folder as salon_tracker.py.")
        sys.exit()

    required_columns = [
        "appointment_id",
        "date",
        "customer_name",
        "service",
        "stylist",
        "price",
        "status"
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        print("\nERROR: Your CSV is missing these columns:")
        print(", ".join(missing_columns))
        sys.exit()

    # Convert date and price to correct formats
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Remove rows with missing date or price
    df = df.dropna(subset=["date", "price"])

    # Clean text values
    df["customer_name"] = df["customer_name"].astype(str).str.strip()
    df["service"] = df["service"].astype(str).str.strip()
    df["stylist"] = df["stylist"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip().str.title()

    # Add helpful date columns
    df["weekday"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.strftime("%B")
    df["year_month"] = df["date"].dt.to_period("M").astype(str)

    return df


# -----------------------------
# BUSINESS ANALYSIS
# -----------------------------
def analyse_salon_data(df):
    """Calculate key salon business insights."""

    completed = df[df["status"] == "Completed"].copy()
    no_shows = df[df["status"] == "No-Show"].copy()
    cancelled = df[df["status"] == "Cancelled"].copy()

    total_appointments = len(df)
    completed_appointments = len(completed)
    total_revenue = completed["price"].sum()

    no_show_rate = 0
    if total_appointments > 0:
        no_show_rate = (len(no_shows) / total_appointments) * 100

    cancellation_rate = 0
    if total_appointments > 0:
        cancellation_rate = (len(cancelled) / total_appointments) * 100

    average_spend = 0
    if completed_appointments > 0:
        average_spend = total_revenue / completed_appointments

    print("\n" + "=" * 55)
    print("SALON APPOINTMENT TRACKER: BUSINESS REPORT")
    print("=" * 55)

    print(f"\nTotal appointments: {total_appointments}")
    print(f"Completed appointments: {completed_appointments}")
    print(f"No-shows: {len(no_shows)}")
    print(f"Cancelled appointments: {len(cancelled)}")
    print(f"No-show rate: {no_show_rate:.2f}%")
    print(f"Cancellation rate: {cancellation_rate:.2f}%")
    print(f"Total revenue: KES {total_revenue:,.2f}")
    print(f"Average customer spend: KES {average_spend:,.2f}")

    # Most popular service
    popular_services = completed["service"].value_counts()

    print("\n--- MOST POPULAR SERVICES ---")
    if not popular_services.empty:
        print(popular_services)
        print(f"\nMost popular service: {popular_services.index[0]}")
    else:
        print("No completed appointments found.")

    # Revenue by service
    revenue_by_service = completed.groupby("service")["price"].sum().sort_values(ascending=False)

    print("\n--- REVENUE BY SERVICE ---")
    print(revenue_by_service)

    # Best-performing stylist
    revenue_by_stylist = completed.groupby("stylist")["price"].sum().sort_values(ascending=False)

    print("\n--- REVENUE BY STYLIST ---")
    print(revenue_by_stylist)

    if not revenue_by_stylist.empty:
        print(f"\nBest-performing stylist: {revenue_by_stylist.index[0]}")

    # Busiest day
    weekday_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ]

    appointments_by_day = df["weekday"].value_counts().reindex(weekday_order, fill_value=0)

    print("\n--- APPOINTMENTS BY DAY ---")
    print(appointments_by_day)

    busiest_day = appointments_by_day.idxmax()
    print(f"\nBusiest day: {busiest_day}")

    # Customers with repeated no-shows
    repeated_no_shows = no_shows["customer_name"].value_counts()
    repeated_no_shows = repeated_no_shows[repeated_no_shows > 1]

    print("\n--- CUSTOMERS WITH REPEATED NO-SHOWS ---")
    if repeated_no_shows.empty:
        print("No customers have more than one no-show.")
    else:
        print(repeated_no_shows)

    # Key recommendation
    print("\n--- BUSINESS RECOMMENDATION ---")

    if no_show_rate >= 20:
        print(
            "The no-show rate is high. The salon should send appointment "
            "reminders by SMS or WhatsApp one day before each appointment."
        )
    else:
        print(
            "The no-show rate is manageable. Continue using reminders and "
            "monitor missed appointments every month."
        )

    if not popular_services.empty:
        print(
            f"The salon should ensure enough staff and supplies are available "
            f"for '{popular_services.index[0]}', the most requested service."
        )

    return {
        "completed": completed,
        "popular_services": popular_services,
        "revenue_by_service": revenue_by_service,
        "revenue_by_stylist": revenue_by_stylist,
        "appointments_by_day": appointments_by_day,
        "no_shows": no_shows
    }


# -----------------------------
# CREATE CHARTS
# -----------------------------
def create_charts(results):
    """Create and save charts in the outputs folder."""

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Chart 1: Popular services
    if not results["popular_services"].empty:
        plt.figure(figsize=(9, 5))
        results["popular_services"].plot(kind="bar", color="mediumpurple")
        plt.title("Most Popular Salon Services")
        plt.xlabel("Service")
        plt.ylabel("Completed Appointments")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_FOLDER}/popular_services.png")
        plt.close()

    # Chart 2: Revenue by service
    if not results["revenue_by_service"].empty:
        plt.figure(figsize=(9, 5))
        results["revenue_by_service"].plot(kind="bar", color="mediumseagreen")
        plt.title("Revenue by Salon Service")
        plt.xlabel("Service")
        plt.ylabel("Revenue (KES)")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_FOLDER}/revenue_by_service.png")
        plt.close()

    # Chart 3: Revenue by stylist
    if not results["revenue_by_stylist"].empty:
        plt.figure(figsize=(9, 5))
        results["revenue_by_stylist"].plot(kind="bar", color="coral")
        plt.title("Revenue Generated by Each Stylist")
        plt.xlabel("Stylist")
        plt.ylabel("Revenue (KES)")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_FOLDER}/revenue_by_stylist.png")
        plt.close()

    # Chart 4: Appointments by day
    plt.figure(figsize=(10, 5))
    results["appointments_by_day"].plot(kind="bar", color="skyblue")
    plt.title("Salon Appointments by Day of the Week")
    plt.xlabel("Day")
    plt.ylabel("Number of Appointments")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_FOLDER}/appointments_by_day.png")
    plt.close()

    print(f"\nCharts saved successfully in the '{OUTPUT_FOLDER}' folder.")


# -----------------------------
# SAVE CLEANED DATA
# -----------------------------
def save_cleaned_data(df):
    """Save a cleaned version of the data for future use."""

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    df.to_csv(f"{OUTPUT_FOLDER}/cleaned_appointments.csv", index=False)
    print("Cleaned appointment data saved successfully.")


# -----------------------------
# MAIN PROGRAM
# -----------------------------
def main():
    print("\nLoading salon appointment data...")

    salon_data = load_data(DATA_FILE)
    results = analyse_salon_data(salon_data)

    save_cleaned_data(salon_data)
    create_charts(results)

    print("\nProject complete. Check the outputs folder for your charts.")


if __name__ == "__main__":
    main()