# 📊 Tableau Metadata Analysis with Python

This repository demonstrates how to use the `tableauserverclient` Python module to analyze Tableau metadata and proactively manage dependencies on your data warehouse.

When changes are made to underlying tables in the warehouse, dashboards or data sources depending on them can silently break. Rather than waiting for a refresh extract to fail or for stakeholders to raise issues, this tool allows data teams to **identify impacted data sources in advance** and **notify owners proactively**.

👉 [Read the related blog post on Medium](https://medium.com/zenjob-tech-blog/metabase-data-management-made-easy-with-python-a332d4c364e3)

---

## 🚀 Features

- Analyze Tableau metadata using Tableau Server Client (`tableauserverclient`)
- Identify which dashboards or data sources rely on specific warehouse tables
- Notify owners before changes are made to data models
- Customize queries and logic to suit your data environment

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.x
- `tableauserverclient` module
- Access to your Tableau Server or Tableau Online instance

### Setup

1. **Clone or download** this repository.
2. **Create a Personal Access Token** in your Tableau account:
   - Go to **My Account Settings** → **Personal Access Tokens**
   - Save the `Token Name` and `Token Secret`
3. **Update credentials** in the script:
   ```python
   token_name = '<API_TOKEN_NAME>'
   token_secret = '<TOKEN_KEY>'
   site_id = '<YOUR_SITE>'
4. Run the script to generate metadata insights.
5. Customize the SQL queries and filtering logic to match your environment and use case.

## 🔍 Customization Tips
- Modify queries to focus on specific schemas, projects, or owners.
- Extend the logic to send email alerts to affected dashboard owners.
- Integrate with CI/CD pipelines for continuous metadata validation.
