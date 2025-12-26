# Streamlit Cloud + Google Sheets setup

## 1) Put these files in your GitHub repo
- `sort_my_money_app_sheets.py` (rename to `sort_my_money_app.py` if you want)
- `requirements.txt`

## 2) Create a Google Cloud service account
- Create a project in Google Cloud Console
- Enable **Google Sheets API** and (recommended) **Google Drive API**
- Create a **Service Account**
- Create a **JSON key** and download it

## 3) Share your Google Sheet with the service account
Sheet ID: `1TWrxq6QrTNYqX0Hgxp3IPCGoDejy5Mzi0rTX4iA60e0`
- Open the sheet
- Share → add the service account email (ends with `iam.gserviceaccount.com`) as **Editor**

## 4) Add Streamlit secrets
In Streamlit Cloud → App → Settings → Secrets, add:

```toml
SHEET_ID = "1TWrxq6QrTNYqX0Hgxp3IPCGoDejy5Mzi0rTX4iA60e0"

[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

## 5) First run
In the app sidebar → **Initialize Sheet**
- Click **Populate plan tabs from Excel**
- Click **Seed assets snapshot**

Then start using:
- Weekly Inputs (expenses + freelance)
- Stocks Update (manual weekly value)
- Assets Snapshot (gold grams, SAR, business, etc.)