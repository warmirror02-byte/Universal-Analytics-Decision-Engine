# Universal-Analytics-Decision-Engine
Overview

The Universal Analytics Decision Engine is a data-agnostic, self-service analytics tool designed to help business users analyze any dataset without SQL, BI tools, or technical expertise.

Unlike traditional dashboards, this system adapts to any schema, any department, and any user, using semantic modeling and rule-based analytics to deliver trustworthy insights.

🎯 Key Problems Solved

Data varies across teams and departments

Column names are inconsistent

Business users rely heavily on analysts

BI tools break with large or unfamiliar datasets

AI tools hallucinate metrics and logic

✅ Core Design Principles

Data-agnostic (no hardcoded column names)

Deterministic analytics (rules before AI)

Scalable filtering (handles large cardinality)

Trust-first results (no silent assumptions)

AI for explanation, not calculation

🧠 System Architecture
Data Upload
   ↓
Semantic Mapping (metrics & dimensions)
   ↓
Filter Context (search-based, scalable)
   ↓
Question Classification
   ↓
Calculation Engine
   ↓
AI Explanation Layer

🔑 Semantic Mapping

Users map dataset columns into:

Metrics: revenue, quantity, discount, cost, etc.

Dimensions: date, category, product, customer, region

This one-time step allows the system to work across any dataset.

🔍 Filter System

Search-based filtering

“Apply all matched results”

No checkbox explosion

Handles thousands of unique values efficiently

🧮 Supported Analysis Types

Totals (SUM, AVG, COUNT, etc.)

Comparisons (time-based)

Breakdowns (group-by)

Trends

Driver analysis

Anomaly detection (planned)

🤖 AI Integration

AI is used only for:

Explaining results

Summarizing insights

Suggesting next analytical questions

All calculations remain rule-based and deterministic.

🛠 Tech Stack

Python

Pandas

Streamlit

SQL-style analytics

Semantic modeling

Rule-based NLP

🚀 Future Enhancements

Multi-table joins

Forecasting

Saved views

Exportable dashboards
