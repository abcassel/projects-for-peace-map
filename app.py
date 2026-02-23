import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- PAGE CONFIG ---
st.set_page_config(page_title="Projects for Peace Map", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("projects_data.csv")
        # Clean headers to prevent KeyErrors
        df.columns = df.columns.str.strip().str.capitalize()
        return df
    except FileNotFoundError:
        st.error("CSV file not found. Please ensure 'projects_data.csv' is in your repository.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter & Search")

    # 1. Region Filter
    region_list = ["All"] + sorted(df["Region"].unique().tolist())
    selected_region = st.sidebar.selectbox("Select a Region:", region_list)

    # 2. Text Search Filter
    search_query = st.sidebar.text_input("Search Project Titles:", "").lower()

    # Apply Logic
    filtered_df = df.copy()
    if selected_region != "All":
        filtered_df = filtered_df[filtered_df["Region"] == selected_region]
    
    if search_query:
        filtered_df = filtered_df[filtered_df["Project_title"].str.lower().contains(search_query, na=False)]

    # --- MAIN UI ---
    st.title(f"Projects for Peace Map")
    if selected_region != "All":
        st.subheader(f"Showing projects in: {selected_region}")

    # Initialize map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    # Add markers
    for idx, row in filtered_df.iterrows():
        # CLEANING QUOTES: .strip('"') removes outer quotes from the CSV data
        raw_title = str(row['Project_title']).strip('"')
        raw_description = str(row['Description']).strip('"')
        
        # HTML for popup (no extra quotes added here)
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 200px;">
            <h4 style="margin-bottom: 5px; color: #1f77b4;">{raw_title}</h4>
            <p style="font-size: 12px; color: #555;"><b>Region:</b> {row['Region']}</p>
            <hr style="margin: 10px 0;">
            <p style="font-size: 13px; line-height: 1.4;">{raw_description}</p>
        </div>
        """
        
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=raw_title
        ).add_to(m)

    # Render map
    st_folium(m, width="100%", height=600)

    # Optional Table
    with st.expander("View Filtered Data Table"):
        st.dataframe(filtered_df)
else:
    st.warning("Upload or connect your data to begin.")
