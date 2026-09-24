# dashboard.py
# Interactive Salon Appointment Tracker Dashboard (SQLite CRUD + Analytics)

import sqlite3
from pathlib import Path
from datetime import datetime, time

import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------------------------------
# APP SETTINGS
# ------------------------------------------------
st.set_page_config(
    page_title="Salon Appointment Tracker",
    page_icon="💇",
    layout="wide"
)

DATABASE_FILE = "salon.db"
STATUSES = ["Completed", "No-Show", "Cancelled"]


# ------------------------------------------------
# DATABASE & DATA PROCESSING FUNCTIONS
# ------------------------------------------------
def get_connection():
    """Connect to the SQLite database."""
    return sqlite3.connect(DATABASE_FILE)


@st.cache_data
def load_appointments():
    """Retrieve and clean all appointment records from salon.db."""
    connection = get_connection()

    query = """
        SELECT
            appointment_id,
            date,
            appointment_time,
            customer_name,
            service,
            stylist,
            price,
            status
        FROM appointments
        ORDER BY date DESC, appointment_time DESC
    """

    df = pd.read_sql_query(query, connection)
    connection.close()

    # Data type formatting and transformations
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Clean text columns
    for col in ["customer_name", "service", "stylist", "status"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Make status names consistent
    df["status"] = (
        df["status"]
        .str.lower()
        .replace({
            "no-show": "No-Show",
            "no show": "No-Show",
            "noshow": "No-Show"
        })
        .str.title()
    )

    # Useful date aggregations
    df["weekday"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.strftime("%B")
    df["year_month"] = df["date"].dt.strftime("%Y-%m")

    return df


def refresh_data():
    """Clear saved dashboard data and reload it."""
    st.cache_data.clear()
    st.rerun()


def convert_to_time(time_value):
    """Convert text such as 09:30 to a Python time value."""
    time_text = str(time_value).strip()

    for time_format in ["%H:%M", "%H:%M:%S"]:
        try:
            return datetime.strptime(time_text, time_format).time()
        except ValueError:
            pass

    return time(9, 0)


def calculate_metrics(data):
    """Calculate summary values for the selected data."""
    completed = data[data["status"] == "Completed"]
    no_shows = data[data["status"] == "No-Show"]
    cancelled = data[data["status"] == "Cancelled"]

    total_appointments = len(data)
    completed_count = len(completed)
    total_revenue = completed["price"].sum()
    average_spend = completed["price"].mean() if completed_count > 0 else 0

    no_show_rate = (
        len(no_shows) / total_appointments * 100
        if total_appointments > 0 else 0
    )

    cancellation_rate = (
        len(cancelled) / total_appointments * 100
        if total_appointments > 0 else 0
    )

    return {
        "completed": completed,
        "no_shows": no_shows,
        "total_appointments": total_appointments,
        "completed_count": completed_count,
        "total_revenue": total_revenue,
        "average_spend": average_spend,
        "no_show_rate": no_show_rate,
        "cancellation_rate": cancellation_rate
    }
def get_client_records(client_identifier):
    """
    Retrieve specific client appointment history by name or appointment ID.
    Supports exact match, partial name match, or exact ID lookups.
    """
    conn = sqlite3.connect("salon.db")

    # SQL query supporting exact ID match or fuzzy customer name search
    query = """
        SELECT 
            appointment_id,
            date,
            appointment_time,
            customer_name,
            service,
            stylist,
            price,
            status
        FROM appointments
        WHERE LOWER(customer_name) LIKE LOWER(?) 
           OR CAST(appointment_id AS TEXT) = ?
        ORDER BY date DESC, appointment_time DESC
    """

    search_term = f"%{client_identifier.strip()}%"
    exact_id_term = client_identifier.strip()

    df_client = pd.read_sql_query(
        query, conn, params=(search_term, exact_id_term)
    )
    conn.close()

    # Format data types
    if not df_client.empty:
        df_client["date"] = pd.to_datetime(df_client["date"]).dt.strftime(
            "%Y-%m-%d"
        )
        df_client["price"] = pd.to_numeric(
            df_client["price"], errors="coerce"
        ).fillna(0)

    return df_client


# ------------------------------------------------
# CHECK DATABASE EXISTANCE & DATA LOAD
# ------------------------------------------------
if not Path(DATABASE_FILE).exists():
    st.error(
        "salon.db was not found. Please ensure salon.db exists in the same folder as dashboard.py."
    )
    st.stop()

df = load_appointments()

if df.empty:
    st.warning("Your salon database has no appointment records yet.")
    st.stop()


# ------------------------------------------------
# HEADER
# ------------------------------------------------
st.title("💇 Salon Appointment Tracker")
st.caption(
    "Use appointment data to understand revenue, popular services, "
    "staff performance, missed appointments, and manage records."
)


# ------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------
st.sidebar.header("Filter Dashboard")

minimum_date = df["date"].min().date()
maximum_date = df["date"].max().date()

selected_dates = st.sidebar.date_input(
    "Select date range",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date
)

selected_services = st.sidebar.multiselect(
    "Select service(s)",
    options=sorted(df["service"].unique()),
    default=sorted(df["service"].unique())
)

selected_stylists = st.sidebar.multiselect(
    "Select stylist(s)",
    options=sorted(df["stylist"].unique()),
    default=sorted(df["stylist"].unique())
)

selected_statuses = st.sidebar.multiselect(
    "Select appointment status",
    options=STATUSES,
    default=STATUSES
)

# Handle date-range selection safely
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates

filtered_data = df[
    (df["date"].dt.date >= start_date)
    & (df["date"].dt.date <= end_date)
    & (df["service"].isin(selected_services))
    & (df["stylist"].isin(selected_stylists))
    & (df["status"].isin(selected_statuses))
].copy()

if filtered_data.empty:
    st.warning("No appointments match your selected filters.")
    st.stop()

metrics = calculate_metrics(filtered_data)
completed = metrics["completed"]
no_shows = metrics["no_shows"]


# ------------------------------------------------
# KPI CARDS
# ------------------------------------------------
st.subheader("Salon Performance Summary")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Appointments", metrics["total_appointments"])
col2.metric("Completed", metrics["completed_count"])
col3.metric("Revenue", f"KES {metrics['total_revenue']:,.0f}")
col4.metric("Average Spend", f"KES {metrics['average_spend']:,.0f}")
col5.metric("No-Show Rate", f"{metrics['no_show_rate']:.1f}%")


# ------------------------------------------------
# TABS SETUP
# ------------------------------------------------
(
    overview_tab,
    performance_tab,
    no_show_tab,
    data_tab,
    create_tab,
    update_tab,
    delete_tab
) = st.tabs([
    "📊 Overview",
    "👩‍💼 Services & Stylists",
    "⚠️ No-Show Analysis",
    "🗂️ Appointment Data",
    "➕ Create",
    "✏️ Update",
    "🗑️ Delete"
])


# ------------------------------------------------
# OVERVIEW TAB
# ------------------------------------------------
with overview_tab:
    st.subheader("Appointments by Status")

    status_counts = (
        filtered_data["status"]
        .value_counts()
        .reset_index()
    )
    status_counts.columns = ["Status", "Appointments"]

    chart_one, chart_two = st.columns(2)

    with chart_one:
        status_chart = px.pie(
            status_counts,
            names="Status",
            values="Appointments",
            color="Status",
            color_discrete_map={
                "Completed": "#2E8B57",
                "No-Show": "#E63946",
                "Cancelled": "#F4A261"
            },
            title="Appointment Status Distribution"
        )
        st.plotly_chart(status_chart, use_container_width=True)

    with chart_two:
        weekday_order = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]

        appointments_by_day = (
            filtered_data["weekday"]
            .value_counts()
            .reindex(weekday_order, fill_value=0)
            .reset_index()
        )
        appointments_by_day.columns = ["Day", "Appointments"]

        day_chart = px.bar(
            appointments_by_day,
            x="Day",
            y="Appointments",
            color="Appointments",
            color_continuous_scale="Purples",
            title="Appointments by Day of the Week"
        )
        st.plotly_chart(day_chart, use_container_width=True)

    st.subheader("Monthly Revenue")

    monthly_revenue = (
        completed.groupby("year_month")["price"]
        .sum()
        .reset_index()
    )
    monthly_revenue.columns = ["Month", "Revenue"]

    if not monthly_revenue.empty:
        monthly_chart = px.line(
            monthly_revenue,
            x="Month",
            y="Revenue",
            markers=True,
            title="Completed Appointment Revenue Over Time"
        )
        monthly_chart.update_traces(line_color="#7B2CBF")
        st.plotly_chart(monthly_chart, use_container_width=True)


# ------------------------------------------------
# SERVICES AND STYLISTS TAB
# ------------------------------------------------
with performance_tab:
    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Most Popular Services")

        service_count = (
            completed["service"]
            .value_counts()
            .reset_index()
        )
        service_count.columns = ["Service", "Completed Appointments"]

        if not service_count.empty:
            service_chart = px.bar(
                service_count,
                x="Service",
                y="Completed Appointments",
                color="Completed Appointments",
                color_continuous_scale="Purples",
                title="Popular Services"
            )
            st.plotly_chart(service_chart, use_container_width=True)

    with right_column:
        st.subheader("Revenue by Service")

        service_revenue = (
            completed.groupby("service")["price"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        service_revenue.columns = ["Service", "Revenue"]

        if not service_revenue.empty:
            revenue_chart = px.bar(
                service_revenue,
                x="Service",
                y="Revenue",
                color="Revenue",
                color_continuous_scale="Greens",
                title="Revenue Generated by Service"
            )
            st.plotly_chart(revenue_chart, use_container_width=True)

    st.subheader("Stylist Performance")

    stylist_performance = (
        completed.groupby("stylist")
        .agg(
            Completed_Appointments=("appointment_id", "count"),
            Revenue=("price", "sum"),
            Average_Customer_Spend=("price", "mean")
        )
        .sort_values("Revenue", ascending=False)
        .reset_index()
    )

    st.dataframe(
        stylist_performance.style.format({
            "Revenue": "KES {:,.0f}",
            "Average_Customer_Spend": "KES {:,.0f}"
        }),
        use_container_width=True
    )

    if not stylist_performance.empty:
        stylist_chart = px.bar(
            stylist_performance,
            x="stylist",
            y="Revenue",
            color="Revenue",
            color_continuous_scale="Oranges",
            title="Revenue Generated by Each Stylist"
        )
        st.plotly_chart(stylist_chart, use_container_width=True)


# ------------------------------------------------
# NO-SHOW TAB
# ------------------------------------------------
with no_show_tab:
    st.subheader("No-Show and Cancellation Analysis")

    no_show_col, cancellation_col = st.columns(2)

    with no_show_col:
        st.metric("No-Show Rate", f"{metrics['no_show_rate']:.1f}%")

    with cancellation_col:
        st.metric(
            "Cancellation Rate",
            f"{metrics['cancellation_rate']:.1f}%"
        )

    repeated_no_shows = (
        no_shows["customer_name"]
        .value_counts()
        .reset_index()
    )
    repeated_no_shows.columns = ["Customer", "No-Shows"]
    repeated_no_shows = repeated_no_shows[
        repeated_no_shows["No-Shows"] >= 2
    ]

    st.subheader("Customers With Repeated No-Shows")

    if repeated_no_shows.empty:
        st.success("No customer has more than one no-show in this selection.")
    else:
        st.dataframe(repeated_no_shows, use_container_width=True)

    st.subheader("Aha! Business Insight")

    if not completed.empty:
        most_popular_service = completed["service"].value_counts().index[0]
        best_stylist = (
            completed.groupby("stylist")["price"]
            .sum()
            .idxmax()
        )
        busiest_day = filtered_data["weekday"].value_counts().index[0]

        st.info(
            f"The salon's biggest opportunity is to focus on "
            f"**{most_popular_service}**, its most popular service, "
            f"ensure enough staff are available on **{busiest_day}**, "
            f"and learn from **{best_stylist}**, the highest revenue "
            f"stylist. Reducing the {metrics['no_show_rate']:.1f}% "
            f"no-show rate through reminders could also protect income."
        )


# ------------------------------------------------
# DATA TAB
# ------------------------------------------------
with data_tab:
    st.subheader("Filtered Appointment Records")

    display_columns = [
        "appointment_id",
        "date",
        "customer_name",
        "service",
        "stylist",
        "price",
        "status"
    ]

    if "appointment_time" in filtered_data.columns:
        display_columns.insert(2, "appointment_time")

    st.dataframe(
        filtered_data[display_columns].sort_values("date", ascending=False),
        use_container_width=True
    )

    csv_download = filtered_data[display_columns].to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_download,
        file_name="filtered_salon_appointments.csv",
        mime="text/csv"
    )


# ------------------------------------------------
# CREATE APPOINTMENT TAB
# ------------------------------------------------
with create_tab:
    st.subheader("Create a New Appointment")

    with st.form("create_appointment_form", clear_on_submit=True):
        customer_name = st.text_input("Customer name")

        service = st.selectbox(
            "Service",
            options=sorted(df["service"].unique())
        )

        stylist = st.selectbox(
            "Stylist",
            options=sorted(df["stylist"].unique())
        )

        appointment_date = st.date_input("Appointment date")
        appointment_time = st.time_input("Appointment time")

        price = st.number_input(
            "Price (KES)",
            min_value=0.0,
            step=100.0
        )

        status = st.selectbox("Status", options=STATUSES)

        create_button = st.form_submit_button("Save Appointment")

        if create_button:
            if not customer_name.strip():
                st.error("Enter the customer's name.")
            elif price <= 0:
                st.error("Price must be greater than zero.")
            else:
                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute("""
                    INSERT INTO appointments (
                        date,
                        appointment_time,
                        customer_name,
                        service,
                        stylist,
                        price,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    appointment_date.strftime("%Y-%m-%d"),
                    appointment_time.strftime("%H:%M"),
                    customer_name.strip(),
                    service,
                    stylist,
                    price,
                    status
                ))

                connection.commit()
                connection.close()

                st.success("Appointment created successfully.")
                refresh_data()

 # ------------------------------------------------
# RETRIEVE SPECIFIC CLIENT DATA
# ------------------------------------------------
st.subheader("🔎 Client Profile & History Lookup")

# Input field for searching specific client
client_query = st.text_input(
    "Search Specific Client",
    placeholder="Enter client name (e.g., Jane Doe) or Appointment ID...",
    key="client_search_input"
)

if client_query.strip():
    client_df = get_client_records(client_query)

    if not client_df.empty:
        # Client Summary Metrics
        total_visits = len(client_df)
        completed_visits = len(client_df[client_df["status"] == "Completed"])
        total_spent = client_df[client_df["status"] == "Completed"]["price"].sum()
        frequent_service = (
            client_df["service"].mode()[0]
            if not client_df["service"].empty
            else "N/A"
        )

        st.markdown(
            f"### Client Summary for **{client_df['customer_name'].iloc[0]}**"
        )

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Total Bookings", total_visits)
        m_col2.metric("Completed Visits", completed_visits)
        m_col3.metric("Total Lifetime Spend", f"KES {total_spent:,.0f}")
        m_col4.metric("Favorite Service", frequent_service)

        st.markdown("---")

        # Detailed History Table
        st.write("#### Detailed Appointment History")
        st.dataframe(
            client_df,
            use_container_width=True,
            column_config={
                "appointment_id": "ID",
                "date": "Date",
                "appointment_time": "Time",
                "customer_name": "Customer Name",
                "service": "Service",
                "stylist": "Stylist",
                "price": st.column_config.NumberColumn(
                    "Price", format="KES %d"
                ),
                "status": "Status",
            },
        )

        # CSV Export for the specific client
        csv = client_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📥 Export {client_query}'s History to CSV",
            data=csv,
            file_name=f"client_history_{client_query.replace(' ', '_')}.csv",
            mime="text/csv",
        )
    else:
        st.info(f"No records found matching **'{client_query}'**.")
else:
    st.info("Type a client name or appointment ID above to retrieve their individual history.")

# ------------------------------------------------
# UPDATE APPOINTMENT TAB
# ------------------------------------------------
with update_tab:
    st.subheader("Update an Appointment")

    selected_id = st.selectbox(
        "Choose appointment ID to edit",
        options=sorted(df["appointment_id"].tolist())
    )

    selected_record = df[
        df["appointment_id"] == selected_id
    ].iloc[0]

    with st.form("update_appointment_form"):
        updated_customer_name = st.text_input(
            "Customer name",
            value=selected_record["customer_name"]
        )

        updated_service = st.selectbox(
            "Service",
            options=sorted(df["service"].unique()),
            index=sorted(df["service"].unique()).index(
                selected_record["service"]
            )
        )

        updated_stylist = st.selectbox(
            "Stylist",
            options=sorted(df["stylist"].unique()),
            index=sorted(df["stylist"].unique()).index(
                selected_record["stylist"]
            )
        )

        updated_date = st.date_input(
            "Appointment date",
            value=selected_record["date"].date()
        )

        updated_time = st.time_input(
            "Appointment time",
            value=convert_to_time(selected_record["appointment_time"])
        )

        updated_price = st.number_input(
            "Price (KES)",
            min_value=0.0,
            value=float(selected_record["price"]),
            step=100.0
        )

        updated_status = st.selectbox(
            "Status",
            options=STATUSES,
            index=STATUSES.index(selected_record["status"])
            if selected_record["status"] in STATUSES else 0
        )

        update_button = st.form_submit_button("Update Appointment")

        if update_button:
            if not updated_customer_name.strip():
                st.error("Enter the customer's name.")
            elif updated_price <= 0:
                st.error("Price must be greater than zero.")
            else:
                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute("""
                    UPDATE appointments
                    SET
                        date = ?,
                        appointment_time = ?,
                        customer_name = ?,
                        service = ?,
                        stylist = ?,
                        price = ?,
                        status = ?
                    WHERE appointment_id = ?
                """, (
                    updated_date.strftime("%Y-%m-%d"),
                    updated_time.strftime("%H:%M"),
                    updated_customer_name.strip(),
                    updated_service,
                    updated_stylist,
                    updated_price,
                    updated_status,
                    selected_id
                ))

                connection.commit()
                connection.close()

                st.success(f"Appointment #{selected_id} updated successfully.")
                refresh_data()


# ------------------------------------------------
# DELETE APPOINTMENT TAB
# ------------------------------------------------
with delete_tab:
    st.subheader("Delete an Appointment")

    delete_id = st.selectbox(
        "Choose appointment ID to delete",
        options=sorted(df["appointment_id"].tolist()),
        key="delete_appointment_id"
    )

    delete_record = df[
        df["appointment_id"] == delete_id
    ].iloc[0]

    st.warning(
        f"You are about to delete appointment #{delete_id}: "
        f"{delete_record['customer_name']} — "
        f"{delete_record['service']} — "
        f"KES {delete_record['price']:,.0f}"
    )

    confirm_delete = st.checkbox(
        "I understand that this will remove the appointment from salon.db."
    )

    if st.button("Delete Appointment", type="primary"):
        if not confirm_delete:
            st.error("Tick the confirmation box before deleting.")
        else:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute("""
                DELETE FROM appointments
                WHERE appointment_id = ?
            """, (delete_id,))

            connection.commit()
            connection.close()

            st.success(f"Appointment #{delete_id} deleted successfully.")
            refresh_data()
           