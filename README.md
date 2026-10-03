# Egypt Media Vault 🏛️📰

**Egypt Media Vault** is an end-to-end data engineering platform designed to collect, process, store, and analyze news data from major Egyptian digital news portals (such as Youm7 and Masrawy).

---

## 📌 Project Overview
The system automates web scraping from target Egyptian news outlets, cleans and normalizes raw text, loads structured datasets into a Data Warehouse using dimensional modeling, and surface operational and analytical KPIs via an interactive dashboard.

---

## 🏗️ System Architecture & Data Pipeline

1. **Data Ingestion & Scraping:**
   * Automated scrapers extract headlines, article bodies, publication timestamps, authors, and categories.
2. **ETL & Processing:**
   * Text normalization, Arabic text cleaning, deduplication, and staging using Python scripts.
3. **Data Warehousing:**
   * Dimensional data modeling (Star Schema) with Fact and Dimension tables for fast querying.
4. **Analytics & Visualization:**
   * Interactive dashboards displaying publishing trends, peak activity hours, and sentiment/category distributions.

---

## 🛠️ Tech Stack
* **Language:** Python
* **Scraping:** BeautifulSoup / Scrapy / Selenium
* **Data Warehousing & DB:** PostgreSQL / Snowflake / BigQuery
* **Orchestration:** Apache Airflow / Scheduled Cron Jobs
* **Visualization:** Power BI / Looker Studio

---

## 📊 Key Indicators & Metrics (KPIs)
* **Publishing Volume:** Article counts by source, category, and date range.
* **Peak Publishing Hours:** Distribution of news releases across the day.
* **Trending Topics:** Keyword frequency and word cloud analysis.
* **Source Comparison:** Coverage speed and article volume across different portals.
