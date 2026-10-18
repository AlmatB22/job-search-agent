# Projects (fictional sample candidate)

## Rental listings warehouse

A small data warehouse built from public short-term rental listing data. Raw CSV
files land in S3, Airflow loads them into PostgreSQL, and dbt models build a star
schema with listing, host and calendar dimensions. A Tableau workbook on top shows
price and occupancy by neighbourhood.

## Course scheduler

A Flask web app that takes a list of required courses and produces conflict-free
timetables. Uses a backtracking search over section times. Deployed in Docker on a
single small VM; about 200 students used it during one registration period.

## Capstone: sensor anomaly detection

Team capstone project (four students). Collected readings from temperature sensors,
stored them in a time-series table and flagged anomalies with a rolling z-score.
Jordan owned the ingestion service and the alerting rules, and wrote the test suite.
