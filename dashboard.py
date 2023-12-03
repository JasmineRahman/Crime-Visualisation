import streamlit as st
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine
from geopy.geocoders import Nominatim
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import warnings
import time
import requests

# Replace these with your MySQL database credentials
db_username = "root"
db_password = "Jasmine5sql"
db_host = "localhost"
db_port = 3306
db_name = "demo"

# Error handling and connection
try:
    engine = create_engine(f"mysql+mysqlconnector://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}")
    conn = engine.raw_connection()
    query = "SELECT YEAR, `STATE/UT`, DISTRICT, `TOTAL IPC CRIMES` FROM demo.crime_data"
    result = pd.read_sql(query, con=conn)
    df = pd.DataFrame(result)
except Exception as e:
    st.error(f"Error connecting to the database: {str(e)}")
    df = pd.DataFrame()  # Provide an empty DataFrame in case of an error
finally:
    if conn:
        conn.close()

# Check if df is not empty before displaying
if not df.empty:
    # Geocode state names to get approximate latitude and longitude
    geolocator = Nominatim(user_agent="crime_visualization", timeout=10)

    # Cache for geocoding results
    geocode_cache = {}

    # Function to handle geocoding with retry and delay
    def geocode_with_retry(location):
        if location in geocode_cache:
            return geocode_cache[location]

        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)

        # Implementing exponential backoff with retry
        for _ in range(retry_strategy.total + 1):
            try:
                result = geolocator.geocode(location)
                if result and hasattr(result, 'latitude') and hasattr(result, 'longitude'):
                    geocode_cache[location] = {
                        "address": result.address,
                        "latitude": result.latitude,
                        "longitude": result.longitude
                    }
                    return geocode_cache[location]
            except (requests.exceptions.RequestException, AttributeError) as e:
                st.warning(f"Geocoding request failed: {str(e)}")
                time.sleep(retry_strategy.sleep_for())

        st.error(f"Geocoding request failed after retries.")
        return None

    df["geocoding_result"] = df["STATE/UT"].apply(lambda x: geocode_with_retry(x) if x else None)

    # Extract information from the geocoding result
    df["Location_Latitude"] = df["geocoding_result"].apply(lambda loc: loc["latitude"] if loc else None)
    df["Location_Longitude"] = df["geocoding_result"].apply(lambda loc: loc["longitude"] if loc else None)

    # Explicitly specify the datetime format for the YEAR column
    df["YEAR"] = pd.to_datetime(df["YEAR"], errors='coerce', format='%Y')

    # Streamlit app layout
    st.set_page_config(page_title="Crime Visualisation", page_icon=":bar_chart:", layout="wide")
    col1, col2, col3 = st.columns(3)

    # Select Year Range
    with col1:
        year1 = st.selectbox("Start Year", sorted(df["YEAR"].dt.year.unique()))

    with col2:
        year2 = st.selectbox("End Year", sorted(df["YEAR"].dt.year.unique()))

    # Convert the input years to integers
    year1 = int(year1) if year1 else None
    year2 = int(year2) if year2 else None

    # Filter the DataFrame based on the specified range
    df_filtered = df[(df["YEAR"].dt.year >= year1) & (df["YEAR"].dt.year <= year2)].copy()

    st.sidebar.header("Choose Your filter:")

    # Fetch unique values for "STATE/UT" and "DISTRICT" from the original DataFrame
    unique_states = df["STATE/UT"].unique()

    state = st.sidebar.multiselect("Pick the State", unique_states)

    # Update available districts based on the selected state
    if state:
        filtered_districts = df[df["STATE/UT"].isin(state)]["DISTRICT"].unique()
        city = st.sidebar.multiselect("Pick the City", filtered_districts)
    else:
        filtered_districts = df["DISTRICT"].unique()
        city = st.sidebar.multiselect("Pick the City", filtered_districts)

    # Apply state and city filters
    filtered_df = df_filtered[df_filtered["STATE/UT"].isin(state) & df_filtered["DISTRICT"].isin(city)]

    # Debugging statements for "YEAR" and "TOTAL IPC CRIMES" columns
    st.write("Debug - 'YEAR' column after filtering:")
    st.write(filtered_df["YEAR"])

    st.write("Debug - 'TOTAL IPC CRIMES' column:")
    st.write(filtered_df["TOTAL IPC CRIMES"])

    # More debugging statements
    st.write("Filtered DataFrame Overview:")
    st.write(filtered_df.head())

    # Group by YEAR and sum TOTAL IPC CRIMES
    year_df = filtered_df.groupby(by=["YEAR"], as_index=False)["TOTAL IPC CRIMES"].sum()

    # More debugging statements
    st.write("Grouped DataFrame Overview:")
    st.write(year_df.head())

    # Create a bar chart for the selected state, district, and year range
    fig_bar = px.bar(
        year_df,
        x="YEAR",
        y="TOTAL IPC CRIMES",
        text=['${:,.2f}'.format(x) for x in year_df["TOTAL IPC CRIMES"]],
        title=f"Total IPC Crimes in {', '.join(state)} - {', '.join(city)} ({year1}-{year2})",
        template="seaborn"
    )

    # Format y-axis as integers
    fig_bar.update_yaxes(type='linear')

    # Display the bar chart
    col3.plotly_chart(fig_bar, use_container_width=True)

    # Create a map of India using Plotly Express
    fig_map = px.scatter_geo(
        filtered_df.dropna(subset=['Location_Latitude', 'Location_Longitude']),  # Filter out rows with None in Latitude or Longitude
        lat='Location_Latitude',
        lon='Location_Longitude',
        color='TOTAL IPC CRIMES',
        size='TOTAL IPC CRIMES',
        hover_name='DISTRICT',
        color_continuous_scale='reds',
        title=f'Crime Map - {", ".join(state)} ({year1}-{year2})',
        scope='asia',  # Set the map scope to Asia (India is part of Asia)
        projection='natural earth'  # Use natural earth projection for better view
    )

    # Display the map
    st.plotly_chart(fig_map, use_container_width=True)

    df_filtered.index = pd.to_datetime(df_filtered.index, format='%Y-%m-%d', errors='coerce')

    selected_crimes = ["MURDER", "RAPE", "KIDNAPPING & ABDUCTION", "ROBBERY", "BURGLARY", "THEFT"]
    crime_df = df_filtered.groupby(by=df_filtered.index.year, as_index=False)[selected_crimes].sum()


    # Line chart for crime trends over the years
    st.write("Line Chart - Crime Trends Over the Years")
    fig_line = px.line(crime_df, x="YEAR", y=selected_crimes, title="Crime Trends Over the Years")
    st.plotly_chart(fig_line, use_container_width=True)

    # Bar chart for total crimes in each year
    st.write("Bar Chart - Total Crimes Each Year")
    fig_bar = px.bar(crime_df, x="YEAR", y="TOTAL IPC CRIMES", title="Total Crimes Each Year")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Pie chart for the distribution of selected crimes in the latest year
    latest_year_data = df_filtered[df_filtered.index.year == df_filtered.index.year.max()]
    st.write("Pie Chart - Distribution of Crimes (Latest Year)")
    fig_pie = px.pie(
        latest_year_data,
        names=selected_crimes,
        title="Distribution of Crimes (Latest Year)",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Area chart for the cumulative total crimes over the years
    st.write("Area Chart - Cumulative Total Crimes Over the Years")
    crime_df["Cumulative Total Crimes"] = crime_df["TOTAL IPC CRIMES"].cumsum()
    fig_area = px.area(crime_df, x="YEAR", y="Cumulative Total Crimes", title="Cumulative Total Crimes Over the Years")
    st.plotly_chart(fig_area, use_container_width=True)

    # Radar chart for the distribution of crimes by type
    st.write("Radar Chart - Distribution of Crimes by Type")
    fig_radar = px.line_polar(latest_year_data, r=selected_crimes, theta=selected_crimes, line_close=True)
    st.plotly_chart(fig_radar, use_container_width=True)

# Scatter plot for crime distribution based on latitude and longitude
    # Scatter plot for crime distribution based on latitude and longitude
    st.write("Scatter Plot - Crime Distribution Based on Latitude and Longitude")
    fig_scatter = px.scatter_mapbox(
        df_filtered,
        lat="Location_Latitude",
        lon="Location_Longitude",
        color="TOTAL IPC CRIMES",
        size="TOTAL IPC CRIMES",
        hover_name="DISTRICT",
        title="Crime Distribution Based on Latitude and Longitude",
        mapbox_style="carto-positron",  # You can adjust the mapbox_style
        zoom=4,  # Adjust the zoom level to focus on India
        center={"lat": 20.5937, "lon": 78.9629},  # Set the center to India's approximate coordinates
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


    # Donut chart for the percentage of each crime type
    st.write("Donut Chart - Percentage of Each Crime Type")
    fig_donut = px.pie(
        latest_year_data,
        names=selected_crimes,
        title="Percentage of Each Crime Type",
        hole=0.4
    )
    st.plotly_chart(fig_donut, use_container_width=True)

    # Sunburst chart for hierarchical representation of crime data
    st.write("Sunburst Chart - Hierarchical Representation of Crime Data")
    fig_sunburst = px.sunburst(
        latest_year_data,
        path=["STATE/UT", "DISTRICT", "TOTAL IPC CRIMES"],
        title="Hierarchical Representation of Crime Data"
    )
    st.plotly_chart(fig_sunburst, use_container_width=True)

else:
    st.warning("No data available. Please check the database connection.")
