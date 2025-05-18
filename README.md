# Patient Support Mood Tracker - Setup Guide

## Overview

This application allows your Ops team to track the mood of patient support tickets throughout the day. Support agents can log moods with optional notes, and the tool visualizes the emotional trends.

## Features

- Log moods using a dropdown with emoji representations
- Add optional notes to provide context
- Visualize mood distributions with a bar chart
- Filter by date to view historical data
- Auto-refresh functionality to keep the chart up-to-date
- View recent mood entries with timestamps and notes

## Prerequisites

- Python 3.7 or higher
- Google account with access to Google Sheets
- Google Cloud Platform project with Sheets API enabled

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install streamlit pandas plotly gspread oauth2client
```

## Google Sheets API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Sheets API and Google Drive API
4. Create a service account and download the JSON credentials file
5. Rename the file to `credentials.json` and place it in the same directory as this app
6. Share your Google Sheet with the service account email address (found in the credentials file)

Alternatively, you can use Streamlit secrets management to store your credentials:

1. Create a file called `.streamlit/secrets.toml` with the following content:

```toml
[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "YOUR_PRIVATE_KEY"
client_email = "YOUR_CLIENT_EMAIL"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CLIENT_CERT_URL"
```

## Running the Application

Run the application with:

```bash
streamlit run mood_tracker_app.py
```

The application will:
1. Connect to Google Sheets (creating a new sheet if needed)
2. Present a UI for logging moods
3. Display visualizations of the collected data

## Usage

### Logging a Mood
1. Select a mood from the dropdown
2. Add an optional note for context
3. Click "Submit"

### Viewing Visualizations
1. The bar chart shows mood distribution for the selected date
2. Use the date picker to view historical data
3. Recent entries are displayed below the chart

### Settings
- Enable/disable auto-refresh
- Adjust refresh interval (30-300 seconds)

## Customization

To add or modify mood options, edit the `mood_options` dictionary in the main function.

## Troubleshooting

- If you encounter connection issues, verify that your credentials file is correctly set up
- Make sure the service account has been given access to the Google Sheet
- Check that the Google Sheets API and Drive API are enabled in your Google Cloud Console project