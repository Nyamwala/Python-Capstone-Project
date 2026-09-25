# My Python Capstone Project
# Salon Appointment Tracker
Salon Appointment Tracker is a Python toolkit that helps salon owners understand their appointment data: attendance patterns, revenue, popular services and stylist performance.
The project analyses appointment records to surface actionable insights (busiest days, no-show trends, top-earning services and stylists) and stores the cleaned data in SQLite for future querying, without ever altering the original CSV.

## Project Structure
.
├── salon_tracker.py        # Analysis + charts script
├── Create-database.py      # CSV -> SQLite import script
├── appointments.csv        # Input data (you provide this)
├── salon.db                # Auto-generated SQLite database
└── outputs/                # Auto-generated on running salon_tracker.py
    ├── cleaned_appointments.csv
    ├── popular_services.png
    ├── revenue_by_service.png
    ├── revenue_by_stylist.png
    └── appointments_by_day.png

- `salon_tracker.py`: Cleans the CSV, prints a full business report to the console, and saves charts + a cleaned CSV to `outputs/`.
- `Create-database.py`: Validates and imports the same CSV into `salon.db`, upserting records so it can be re-run safely as new appointments come in.

## Requirements

- Python
- [pandas](https://pandas.pydata.org/)
- [matplotlib](https://matplotlib.org/)

`Create-database.py` only relies on Python's built-in `csv` and `sqlite3` modules, so no extra installs are needed to run it on its own.

## Installation

**Clone or download the project**

```bash
git clone https://github.com/<your-username>/salon-appointment-tracker.git
cd salon-appointment-tracker
```

**Create a virtual environment (recommended)**

```bash
python -m venv venv
```

**Activate the virtual environment**

For Windows:
```bash
venv\Scripts\activate
```

For Mac or Linux:
```bash
source venv/bin/activate
```

**Install required packages**

```bash
pip install pandas matplotlib
```

## Step-by-Step Guide: Using the Project

### 1. Project Setup
Make sure your folder matches the structure above, with `salon_tracker.py`, `Create-database.py`, and your appointment data (`appointments.csv` or `Appointments.csv`) all in the same directory.

### 2. Prepare the Data
Your CSV must include these columns:

| Column           | Description                              |
|-------------------|-------------------------------------------|
| `appointment_id`  | Unique ID for the appointment             |
| `date`            | Appointment date (any standard format)    |
| `customer_name`   | Customer's name                           |
| `service`         | Service booked (e.g. Haircut, Manicure)   |
| `stylist`         | Stylist assigned                          |
| `price`           | Price charged (numeric)                   |
| `status`          | Completed / No-Show / Cancelled           |

`Create-database.py` also accepts an optional `appointment_time` column if present.

### 3. Run the Analysis
```bash
python salon_tracker.py
```
This prints a full business report to the console — appointment counts, no-show and cancellation rates, revenue, most popular service, revenue by service/stylist, busiest day, and repeated no-show customers — then saves charts and a cleaned CSV to `outputs/`.

### 4. Build or Update the Database
```bash
python Create-database.py
```
This creates (or updates) `salon.db`, a SQLite database with an `appointments` table indexed on `date`, `stylist`, and `status`. Records are matched by `appointment_id`, so re-running the script after adding new rows to the CSV updates existing entries instead of duplicating them. Invalid or blank rows are skipped and reported in the console.

## Example Usage

- **Get a business report**: Run `python salon_tracker.py` with your appointments CSV in the folder to see revenue, popular services, and no-show trends.
- **Track data over time**: Run `python Create-database.py` after each new batch of appointments to keep `salon.db` up to date for further querying or reporting.
- **Spot problem customers**: Check the "Customers with repeated no-shows" section of the report to decide who might need a reminder call or deposit policy.

## Code Explanation

Both scripts follow the same basic pattern:

1. **Load** the CSV and validate that all required columns are present.
2. **Clean** the data — parsing dates, coercing prices to numbers, normalising text (e.g. status values like "no show" / "noshow" become `No-Show`), and dropping invalid rows.
3. **Process** the data — `salon_tracker.py` aggregates it into a report and charts; `Create-database.py` inserts/updates it in SQLite.
4. **Report** the outcome — a console summary of what was found, generated, or skipped.

## Notes

- Rows with missing/invalid `date` or `price` values are automatically dropped.
- Revenue figures are displayed in **KES** — update the scripts if you use a different currency.
- The `outputs/` folder and `salon.db` are created automatically if they don't already exist.
- The original CSV is never modified by either script.

## License

Free to use and modify for personal or business purposes.
