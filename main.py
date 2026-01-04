import psycopg2

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def fetch_all(conn, query, params=None):
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cur.close()
    return rows

def confidence_level(change_pct, driver_pct=None):
    if driver_pct is not None and abs(change_pct) >= 20 and driver_pct >= 60:
        return "High"
    if abs(change_pct) >= 10:
        return "Medium"
    return "Low"


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(user_input: str):
    text = user_input.lower()

    if "yesterday" in text or "today" in text or "sales perform" in text:
        return "DAILY_SUMMARY"

    if "unusual" in text or "weird" in text or "anything happen" in text:
        return "ANOMALY_CHECK"

    if "why" in text and ("drop" in text or "increase" in text or "change" in text):
        return "CHANGE_REASON"

    if "which" in text and ("region" in text or "product" in text or "caused" in text):
        return "DRIVER_ANALYSIS"

    return "UNSUPPORTED"


# =========================================================
# DB CONNECTION
# =========================================================

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="analyst_ai",
        user="postgres",
        password="0818"
    )


# =========================================================
# DAILY SUMMARY
# =========================================================

def run_daily_summary(conn):
    query = """
    WITH daily_metrics AS (
        SELECT
            order_date,
            COUNT(order_id) AS orders,
            SUM(revenue) AS revenue,
            SUM(revenue) / COUNT(order_id) AS aov
        FROM sales_transactions
        GROUP BY order_date
    )
    SELECT *
    FROM daily_metrics
    ORDER BY order_date DESC
    LIMIT 2;
    """

    rows = fetch_all(conn, query)

    curr = rows[0]
    prev = rows[1]

    curr_date, curr_orders, curr_revenue, curr_aov = curr
    prev_date, prev_orders, prev_revenue, prev_aov = prev

    change_pct = round(((curr_revenue - prev_revenue) / prev_revenue) * 100, 2)

    print("\nDAILY SALES SUMMARY\n")
    print(f"Date: {curr_date}")
    print(f"Revenue: {curr_revenue}")
    print(f"Orders: {curr_orders}")
    print(f"AOV: {round(curr_aov, 2)}")

    if change_pct > 0:
        print(f"\nRevenue increased by {change_pct}% compared to the previous day.")
    elif change_pct < 0:
        print(f"\nRevenue decreased by {abs(change_pct)}% compared to the previous day.")
    else:
        print("\nRevenue remained flat compared to the previous day.")


# =========================================================
# ANOMALY CHECK
# =========================================================

def run_anomaly_check(conn):
    cur = conn.cursor()

    cur.execute("""
        WITH daily_revenue AS (
            SELECT
                order_date,
                SUM(revenue) AS revenue
            FROM sales_transactions
            GROUP BY order_date
        )
        SELECT
            order_date,
            revenue,
            LAG(revenue) OVER (ORDER BY order_date) AS prev_revenue
        FROM daily_revenue
        ORDER BY order_date DESC
        LIMIT 1;
    """)

    date, revenue, prev_revenue = cur.fetchone()
    cur.close()

    change_pct = round(((revenue - prev_revenue) / prev_revenue) * 100, 2)

    print("\nANOMALY CHECK\n")

    if abs(change_pct) >= 10:
        direction = "increased" if change_pct > 0 else "decreased"
        print(f"Yes. Revenue {direction} significantly by {abs(change_pct)}% on {date}.")
    else:
        print(f"No significant anomalies detected. Revenue changed by only {abs(change_pct)}%.")


# =========================================================
# CHANGE REASON (ORDERS vs AOV)
# =========================================================

def run_change_reason(conn):
    query = """
    WITH daily_metrics AS (
        SELECT
            order_date,
            COUNT(order_id) AS orders,
            SUM(revenue) AS revenue,
            SUM(revenue) / COUNT(order_id) AS aov
        FROM sales_transactions
        GROUP BY order_date
    )
    SELECT *
    FROM daily_metrics
    ORDER BY order_date DESC
    LIMIT 2;
    """

    rows = fetch_all(conn, query)

    curr = rows[0]
    prev = rows[1]

    curr_date, curr_orders, curr_revenue, curr_aov = curr
    prev_date, prev_orders, prev_revenue, prev_aov = prev

    orders_change_pct = round(((curr_orders - prev_orders) / prev_orders) * 100, 2)
    aov_change_pct = round(((curr_aov - prev_aov) / prev_aov) * 100, 2)

    print("\nCHANGE REASON ANALYSIS\n")
    print(f"Orders change: {orders_change_pct}%")
    print(f"AOV change: {aov_change_pct}%\n")

    if orders_change_pct < -5 and abs(aov_change_pct) <= 5:
        reason = "fewer orders (demand issue)"
    elif abs(orders_change_pct) <= 5 and aov_change_pct < -5:
        reason = "lower average order value (pricing or mix issue)"
    elif orders_change_pct < -5 and aov_change_pct < -5:
        reason = "both fewer orders and lower order value (serious performance issue)"
    elif orders_change_pct > 5 and aov_change_pct > 5:
        reason = "both higher demand and higher order value (healthy growth)"
    else:
        reason = "mixed signals with no clear single driver"

    print(f"Primary reason for change: {reason}")


# =========================================================
# DRIVER ANALYSIS (REGION)
# =========================================================

def run_driver_analysis(conn):
    cur = conn.cursor()

    # Get latest two dates
    cur.execute("""
        SELECT DISTINCT order_date
        FROM sales_transactions
        ORDER BY order_date DESC
        LIMIT 2;
    """)
    dates = cur.fetchall()
    curr_date = dates[0][0]
    prev_date = dates[1][0]
    cur.close()

    query = """
    SELECT
        region,
        SUM(CASE WHEN order_date = %s THEN revenue ELSE 0 END) AS curr_revenue,
        SUM(CASE WHEN order_date = %s THEN revenue ELSE 0 END) AS prev_revenue
    FROM sales_transactions
    WHERE order_date IN (%s, %s)
    GROUP BY region;
    """

    rows = fetch_all(conn, query, (curr_date, prev_date, curr_date, prev_date))

    total_change = 0
    region_changes = []

    for region, curr_rev, prev_rev in rows:
        change = curr_rev - prev_rev
        total_change += change
        region_changes.append((region, change))

    print("\nDRIVER ANALYSIS (REGION)\n")

    if total_change == 0:
        print("No overall revenue change detected.")
        return

    primary_driver = None
    max_contribution = 0

    for region, change in region_changes:
        contribution_pct = round((change / total_change) * 100, 2)
        print(f"{region}: change = {change}, contribution = {contribution_pct}%")

        if abs(contribution_pct) > max_contribution:
            max_contribution = abs(contribution_pct)
            primary_driver = region

    print()
    if max_contribution >= 60:
        print(f"Primary driver of change: {primary_driver} region.")
    else:
        print("No single region explains most of the change.")


# =========================================================
# MAIN
# =========================================================

print("=== Analyst AI Started ===")
user_input = input("Ask a question: ")
intent = detect_intent(user_input)
conn = get_connection()

if intent == "DAILY_SUMMARY":
    run_daily_summary(conn)

elif intent == "ANOMALY_CHECK":
    run_anomaly_check(conn)

elif intent == "CHANGE_REASON":
    run_change_reason(conn)

elif intent == "DRIVER_ANALYSIS":
    run_driver_analysis(conn)

else:
    print("This analysis is not supported yet.")

conn.close()
