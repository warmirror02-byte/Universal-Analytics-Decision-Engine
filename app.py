import streamlit as st
import pandas as pd
import re

# =========================
# PAGE CONFIG
# =========================
st.set_page_config("Analyst AI", layout="wide")
st.title("📊 Analyst AI")

# =========================
# CONFIG
# =========================
AGG_KEYWORDS = {
    "total": "sum", "sum": "sum",
    "average": "avg", "avg": "avg", "mean": "avg",
    "max": "max", "minimum": "min", "min": "min",
    "count": "count"
}

METRIC_WORDS = {
    "revenue": ["revenue", "sales", "amount"],
    "quantity": ["quantity", "units", "qty"],
    "discount": ["discount"]
}

# =========================
# SESSION STATE
# =========================
if "schema" not in st.session_state:
    st.session_state.schema = None

if "applied_filters" not in st.session_state:
    st.session_state.applied_filters = {}

# =========================
# HELPERS
# =========================
def detect_metric(q):
    q = q.lower()
    for k, v in METRIC_WORDS.items():
        if any(w in q for w in v):
            return k
    return None

def detect_agg(q):
    q = q.lower()
    for k, v in AGG_KEYWORDS.items():
        if k in q:
            return v
    return "sum"

def detect_explicit_filter(q):
    return dict(re.findall(r"where\s+(\w+)\s*=\s*([\w\s\-]+)", q.lower()))

@st.cache_data(show_spinner=False)
def get_combined_series(df, cols):
    return df[cols].astype(str).agg(" > ".join, axis=1)

# =========================
# APPLY FILTER LOGIC
# =========================
def apply_all_filters(df, schema):
    data = df.copy()

    for dim, selected_values in st.session_state.applied_filters.items():
        if not selected_values:
            continue

        cols = schema.get(dim)
        combined = get_combined_series(data, cols)
        data = data[combined.isin(selected_values)]

    return data

# =========================
# FILE UPLOAD
# =========================
uploaded = st.file_uploader("Upload data file", type=["csv", "xlsx"])
if not uploaded:
    st.stop()

df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
st.subheader("Data Preview")
st.dataframe(df.head(100), height=300)

num_cols = df.select_dtypes(include="number").columns.tolist()
all_cols = df.columns.tolist()

# =========================
# DATASET MAPPING
# =========================
st.subheader("Dataset Mapping")

with st.form("mapping"):
    revenue = st.selectbox("Revenue", ["None"] + num_cols)
    quantity = st.selectbox("Quantity", ["None"] + num_cols)
    discount = st.selectbox("Discount", ["None"] + num_cols)

    category = st.multiselect("Category columns", all_cols)
    product = st.multiselect("Product columns", all_cols)
    customer = st.multiselect("Customer columns", all_cols)

    if st.form_submit_button("Save Mapping"):
        st.session_state.schema = {
            "revenue": revenue if revenue != "None" else None,
            "quantity": quantity if quantity != "None" else None,
            "discount": discount if discount != "None" else None,
            "category": category,
            "product": product,
            "customer": customer
        }
        st.success("Mapping saved")

schema = st.session_state.schema
if not schema:
    st.stop()

# =========================
# FILTER UI (APPLY ALL SEARCH RESULTS)
# =========================
st.subheader("Filters")

def filter_block(df, dim, label):
    cols = schema.get(dim)
    if not cols:
        return

    combined = get_combined_series(df, cols)
    unique_vals = combined.unique().tolist()

    with st.expander(f"{label} Filter"):
        search = st.text_input(f"Search {label}", key=f"search_{dim}")

        if search:
            tokens = [t.lower() for t in search.split() if t.strip()]
            matches = [v for v in unique_vals if all(t in v.lower() for t in tokens)]
        else:
            matches = unique_vals

        st.caption(f"Matched results: {len(matches)}")

        if st.button(f"Apply ALL matched {label}", key=f"apply_{dim}"):
            st.session_state.applied_filters[dim] = set(matches)
            st.success(f"{len(matches)} {label.lower()} applied")

        if dim in st.session_state.applied_filters:
            st.info(f"Active filter: {len(st.session_state.applied_filters[dim])} selected")

        # Preview only (not selection)
        st.markdown("**Preview (first 20)**")
        st.write(matches[:20])

filter_block(df, "category", "Category")
filter_block(df, "product", "Product")
filter_block(df, "customer", "Customer")

# =========================
# QUESTION
# =========================
st.subheader("Ask a Question")
q = st.text_input("Example: total sales, average discount")

if not q:
    st.stop()

metric = detect_metric(q)
agg = detect_agg(q)
text_filters = detect_explicit_filter(q)

if not metric:
    st.error("Metric not detected in question")
    st.stop()

metric_col = schema.get(metric)
if not metric_col:
    st.error(f"{metric} not mapped")
    st.stop()

# =========================
# APPLY FILTERS
# =========================
filtered_df = apply_all_filters(df, schema)

# text filters (where product = X)
for dim, val in text_filters.items():
    cols = schema.get(dim)
    if cols:
        combined = get_combined_series(filtered_df, cols).str.lower()
        filtered_df = filtered_df[combined.str.contains(val.lower())]

# =========================
# RESULT
# =========================
value = getattr(filtered_df[metric_col], agg if agg != "avg" else "mean")()
st.metric(f"{agg.upper()} {metric}", round(value, 2))
