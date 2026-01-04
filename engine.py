import psycopg2
from psycopg2 import sql

# ================= DB =================

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="analyst_ai",
        user="postgres",
        password="0818"
    )

# ================= METRIC SAFETY =================

def resolve_metric(semantic, metric):
    col = semantic["metrics"].get(metric)
    if not col:
        return {"status": "MISSING_METRIC", "metric": metric}
    return {"status": "OK", "column": col}

def detect_aggregation(text):
    t = text.lower()
    if any(x in t for x in ["avg", "average", "mean"]): return "AVG"
    if any(x in t for x in ["min", "minimum", "lowest"]): return "MIN"
    if any(x in t for x in ["max", "maximum", "highest"]): return "MAX"
    if "count" in t or "how many" in t: return "COUNT"
    return "SUM"

# ================= ANALYSIS =================

def basic_summary(conn, semantic, question, metric):
    agg = detect_aggregation(question)
    resolved = resolve_metric(semantic, metric)
    if resolved["status"] != "OK":
        return resolved

    query = sql.SQL("""
        SELECT {agg}((metrics->>{col})::NUMERIC)
        FROM sales_transactions;
    """).format(
        agg=sql.SQL(agg),
        col=sql.Literal(resolved["column"])
    )

    cur = conn.cursor()
    cur.execute(query)
    value = cur.fetchone()[0]
    cur.close()

    return {
        "status": "OK",
        "title": "Summary",
        "content": [f"{agg}({metric}) = {round(value,2) if value else 0}"]
    }

def year_comparison(conn, semantic, question, metric):
    agg = detect_aggregation(question)
    resolved = resolve_metric(semantic, metric)
    if resolved["status"] != "OK":
        return resolved

    query = sql.SQL("""
        SELECT
            EXTRACT(YEAR FROM order_date) AS yr,
            {agg}((metrics->>{col})::NUMERIC)
        FROM sales_transactions
        GROUP BY yr
        ORDER BY yr DESC
        LIMIT 2;
    """).format(
        agg=sql.SQL(agg),
        col=sql.Literal(resolved["column"])
    )

    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()

    if len(rows) < 2:
        return {"status":"OK","title":"Year Comparison","content":["Not enough data"]}

    c, p = rows
    change = round(((c[1]-p[1])/p[1])*100,2) if p[1] else 0

    return {
        "status":"OK",
        "title":"Year Comparison",
        "content":[
            f"{c[0]}: {round(c[1],2)}",
            f"{p[0]}: {round(p[1],2)}",
            f"Change: {change}%"
        ]
    }

def run_analysis(conn, semantic, question, metric):
    if "year" in question.lower():
        return year_comparison(conn, semantic, question, metric)
    return basic_summary(conn, semantic, question, metric)
