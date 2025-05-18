import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- Configuration ---
try:
    creds_json = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
    }
    credentials = Credentials.from_service_account_info(
        creds_json,
        scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
    )
    gc = gspread.authorize(credentials)
except KeyError:
    SERVICE_ACCOUNT_FILE = 'google_credentials.json'
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
    try:
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        gc = gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Failed to load credentials. Ensure 'google_credentials.json' is correctly configured or Streamlit secrets are set. Error: {e}")
        st.stop()

# --- Google Sheet Configuration ---
SHEET_ID_OR_NAME = "1dZu51_KLwO-4ZegdVpjgxuq8764g8U1vpj2sz7eBmRg"
WORKSHEET_NAME = "Sheet1"

# --- Moods ---
MOODS = {
    "😊 Happy": "😊",
    "😠 Frustrated": "😠",
    "😕 Confused": "😕",
    "🎉 Celebratory": "🎉",
    "😥 Sad": "😥",
    "🤔 Thoughtful": "🤔",
    "😴 Tired": "😴"
}
MOOD_EMOJIS = list(MOODS.values())

# --- Helper Functions ---
@st.cache_resource(ttl=600)
def get_worksheet():
    """Connects to Google Sheets and returns the specific worksheet."""
    try:
        sh = gc.open_by_key(SHEET_ID_OR_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{SHEET_ID_OR_NAME}' not found. Please check the name or share it with '{credentials.service_account_email}'.")
        st.stop()
        return None
    
    try:
        worksheet = sh.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Worksheet '{WORKSHEET_NAME}' not found in '{SHEET_ID_OR_NAME}'. Creating it.")
        worksheet = sh.add_worksheet(title=WORKSHEET_NAME, rows="100", cols="20")
        headers = ["Timestamp", "Mood", "Note"]
        if not worksheet.row_values(1):
             worksheet.append_row(headers)
    return worksheet

@st.cache_data(ttl=60)
def get_mood_data(_worksheet):
    """Fetches all mood data from the worksheet and returns it as a DataFrame."""
    if _worksheet is None:
        return pd.DataFrame(columns=["Timestamp", "Mood", "Note"])
    
    data = _worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    for col in ["Timestamp", "Mood", "Note"]:
        if col not in df.columns:
            df[col] = None

    if "Timestamp" in df.columns and not df.empty:
        try:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        except Exception as e:
            st.warning(f"Could not parse all timestamps: {e}. Rows with invalid timestamps might be ignored for filtering.")
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')
    return df

def log_mood_entry(worksheet, mood, note):
    """Appends a new mood entry to the Google Sheet."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        worksheet.append_row([timestamp, mood, note])
        return True
    except Exception as e:
        st.error(f"Failed to log mood: {e}")
        return False

# --- Streamlit App UI ---
st.set_page_config(page_title="Ops Mood Tracker", page_icon="😊", layout="wide")
st.title("😊 Ops Team Mood Tracker")
st.markdown("Log the vibe of the ticket queue and see how we're feeling!")

worksheet = get_worksheet()
if worksheet is None:
    st.error("Could not connect to the Google Sheet. Please check configuration and permissions.")
    st.stop()

# --- 1. Log a Mood ---
st.header("🎤 Log a Mood")
log_col1, log_col2 = st.columns([2,3])

with log_col1:
    selected_mood_display = st.selectbox(
        "How's the queue feeling?",
        options=list(MOODS.keys()),
        index=0
    )
    selected_mood_value = MOODS[selected_mood_display]

with log_col2:
    note = st.text_input("Optional note (e.g., 'lots of Rx delays today')")

if st.button("➕ Log Mood", type="primary"):
    if selected_mood_value:
        if log_mood_entry(worksheet, selected_mood_value, note):
            st.success(f"Mood '{selected_mood_value}' logged with note: '{note if note else 'N/A'}'")
            st.cache_data.clear()
        else:
            st.error("Failed to log mood. Please try again.")
    else:
        st.warning("Please select a mood.")

st.divider()

# --- 2. Visualize the Mood ---
st.header("📊 Mood Dashboard")

all_mood_data_for_datepicker = get_mood_data(worksheet)

min_date_for_input = None

if not all_mood_data_for_datepicker.empty and \
   "Timestamp" in all_mood_data_for_datepicker.columns and \
   not all_mood_data_for_datepicker["Timestamp"].dropna().empty:
    try:
        min_date_for_input = all_mood_data_for_datepicker["Timestamp"].min().date()
    except AttributeError:
        min_date_for_input = None

selected_date_obj = st.date_input(
    "Select a date:",
    value=datetime.today(),
    min_value=min_date_for_input,
    max_value=datetime.today().date(),
    format="YYYY-MM-DD",
    help="Select a date to see the mood breakdown for that day."
)

if st.button("🔄 Refresh Data & Chart"):
    st.cache_data.clear()
    st.cache_resource.clear()

all_mood_data = get_mood_data(worksheet)

if all_mood_data.empty or "Timestamp" not in all_mood_data.columns or all_mood_data["Timestamp"].isnull().all():
    st.info("No mood data logged yet. Start logging to see the chart!")
else:
    all_mood_data_filtered_for_ts = all_mood_data.dropna(subset=['Timestamp'])

    if not all_mood_data_filtered_for_ts.empty and selected_date_obj:
        day_specific_data = all_mood_data_filtered_for_ts[
            all_mood_data_filtered_for_ts['Timestamp'].dt.date == selected_date_obj
        ]

        display_date_str = selected_date_obj.strftime('%B %d, %Y')
        if selected_date_obj == datetime.today().date():
            display_date_str = f"Today ({display_date_str})"

        if not day_specific_data.empty and "Mood" in day_specific_data.columns:
            mood_counts = day_specific_data['Mood'].value_counts().reset_index()
            mood_counts.columns = ['Mood', 'Count']

            all_possible_moods_df = pd.DataFrame({'Mood': MOOD_EMOJIS})
            mood_counts = pd.merge(all_possible_moods_df, mood_counts, on='Mood', how='left').fillna(0)
            mood_counts['Count'] = mood_counts['Count'].astype(int)
            mood_counts = mood_counts.sort_values(by='Mood')

            fig = px.bar(
                mood_counts,
                x='Mood',
                y='Count',
                title=f"Mood Counts for {display_date_str}",
                labels={'Mood': 'Mood Emoji', 'Count': 'Number of Logs'},
                color='Mood',
                color_discrete_map={emoji: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, emoji in enumerate(MOOD_EMOJIS)}
            )
            fig.update_layout(xaxis_title="Mood", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader(f"Logged Entries for {display_date_str}:")
            if not day_specific_data.empty:
                st.dataframe(
                    day_specific_data[['Timestamp', 'Mood', 'Note']]
                    .sort_values(by="Timestamp", ascending=False)
                    .rename(columns={'Timestamp': 'Time of Log'}),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Time of Log": st.column_config.DatetimeColumn(
                            "Time of Log",
                            format="HH:mm:ss",
                        )
                    }
                )
            else:
                st.info(f"No moods logged for {display_date_str} yet.")
        else:
            st.info(f"No moods logged for {display_date_str} yet.")
    elif not selected_date_obj:
        st.warning("Please select a date to view moods.")
    else:
        st.info("No valid timestamp data found in the logs.")

# --- Optional: Display All Data (chronological) ---
with st.expander("📂 View All Logged Data (chronological)"):
    if not all_mood_data.empty:
        if 'Timestamp' in all_mood_data.columns and not pd.api.types.is_datetime64_any_dtype(all_mood_data['Timestamp']):
             all_mood_data_display = all_mood_data.copy()
             all_mood_data_display['Timestamp'] = pd.to_datetime(all_mood_data_display['Timestamp'], errors='coerce')
        else:
            all_mood_data_display = all_mood_data

        st.dataframe(
            all_mood_data_display.sort_values(by="Timestamp", ascending=False).dropna(subset=['Timestamp']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("No data to display.")
