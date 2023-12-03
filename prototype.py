import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# Create a DataFrame with random data for demonstration
np.random.seed(42)
num_rows = 100
random_data = {
    "YEAR": np.random.choice(range(2000, 2023), num_rows),
    "STATE/UT": np.random.choice(["TamilNadu", "Kerala", "Karnataka", "Maharashtra"], num_rows),
    "DISTRICT": np.random.choice(["Madurai", "Cuddalore", "Coimbatore", "cochin"], num_rows),
    "TOTAL IPC CRIMES": np.random.randint(50, 500, num_rows),
    "Location_Latitude": np.random.uniform(8, 37, num_rows),  # Adjusted latitude range for India
    "Location_Longitude": np.random.uniform(68, 98, num_rows),  # Adjusted longitude range for India
    "MURDER": np.random.randint(5, 50, num_rows),
    "RAPE": np.random.randint(5, 50, num_rows),
    "KIDNAPPING & ABDUCTION": np.random.randint(5, 50, num_rows),
    "ROBBERY": np.random.randint(5, 50, num_rows),
    "BURGLARY": np.random.randint(5, 50, num_rows),
    "THEFT": np.random.randint(5, 50, num_rows),
}

df = pd.DataFrame(random_data)

# Constants for Protection Level Calculation
W_Distance = 0.4
W_Size = 0.3
W_Staffing = 0.3

# Streamlit app layout
st.set_page_config(page_title="Crime Visualization Prototype", page_icon=":bar_chart:", layout="wide")

# Display the DataFrame
st.write(df)
st.sidebar.title("Emergency Details")
st.sidebar.markdown("**Emergency Contact Numbers:**")
st.sidebar.markdown("- Police: 100")
st.sidebar.markdown("- Ambulance: 108")
st.sidebar.markdown("- Fire: 101")

st.sidebar.title("Dynamic Filtering Options")
selected_year_range = st.sidebar.slider("Select Year Range", min_value=df["YEAR"].min(), max_value=df["YEAR"].max(), value=(2000, 2022))
selected_state = st.sidebar.multiselect("Select State(s)", df["STATE/UT"].unique())
selected_district = st.sidebar.multiselect("Select District(s)", df["DISTRICT"].unique())

# Apply filters to the DataFrame
filtered_df = df[
    (df["YEAR"].between(selected_year_range[0], selected_year_range[1])) &
    (df["STATE/UT"].isin(selected_state)) &
    (df["DISTRICT"].isin(selected_district))
]

# Function to calculate Protection Level for each location
def calculate_protection_level(distance, size, staffing):
    # You can define your scoring functions based on your specific criteria
    score_distance = 1 / distance  # Example: Inverse distance
    score_size = size / max_size  # Example: Normalized size
    score_staffing = staffing / max_staffing  # Example: Normalized staffing

    protection_level = (
        W_Distance * score_distance +
        W_Size * score_size +
        W_Staffing * score_staffing
    ) / (W_Distance + W_Size + W_Staffing)

    return protection_level

# Calculate max_size and max_staffing
max_size = filtered_df['TOTAL IPC CRIMES'].max()
max_staffing = filtered_df['TOTAL IPC CRIMES'].max()

# Calculate Protection Level for each location
filtered_df['Protection_Level'] = filtered_df.apply(
    lambda row: calculate_protection_level(row['TOTAL IPC CRIMES'], row['TOTAL IPC CRIMES'], row['TOTAL IPC CRIMES']),
    axis=1
)

# Create a map of India using Plotly Express with randomized data
st.write("Scatter Plot - Crime Distribution Based on Latitude and Longitude (India Level)")
fig_scatter = px.scatter_mapbox(
    df,
    lat="Location_Latitude",
    lon="Location_Longitude",
    color="TOTAL IPC CRIMES",
    size="TOTAL IPC CRIMES",
    hover_name="DISTRICT",
    title="Crime Distribution Based on Latitude and Longitude (India Level)",
    mapbox_style="carto-positron",
    zoom=4,  # Adjust the zoom level to focus on India
    center={"lat": 20.5937, "lon": 78.9629},  # Set the center to India's approximate coordinates
)
st.plotly_chart(fig_scatter, use_container_width=True)

# Display Protection Level on the map
st.write("Scatter Plot with Protection Level")
fig_scatter_protection = px.scatter_mapbox(
    filtered_df,
    lat="Location_Latitude",
    lon="Location_Longitude",
    color="Protection_Level",
    size="Protection_Level",
    hover_name="DISTRICT",
    hover_data=["Protection_Level"],
    title="Crime Distribution with Protection Level",
    mapbox_style="carto-positron",
    zoom=4,
    center={"lat": 20.5937, "lon": 78.9629},
)
fig_scatter_protection.update_traces(
    hovertemplate="<b>%{hovertext}</b><br><br>" +
                  "Protection Level: %{marker.size}<br>" +
                  "Total IPC Crimes: %{marker.size}<br>" +
                  "<extra></extra>"
)
st.plotly_chart(fig_scatter_protection, use_container_width=True)

# Display Protection Level below the map
st.write("Protection Levels:")
st.write(filtered_df[['DISTRICT', 'Protection_Level']].set_index('DISTRICT'))


# Group by YEAR and sum selected crime types for randomized data
selected_crimes = ["MURDER", "RAPE", "KIDNAPPING & ABDUCTION", "ROBBERY", "BURGLARY", "THEFT", "TOTAL IPC CRIMES"]
crime_df = df.groupby(by="YEAR", as_index=False)[selected_crimes].sum()

# Line chart for crime trends over the years with randomized data
st.write("Line Chart - Crime Trends Over the Years")
fig_line = px.line(crime_df, x="YEAR", y=selected_crimes, title="Crime Trends Over the Years")
st.plotly_chart(fig_line, use_container_width=True)

# Bar chart for total crimes in each year with randomized data
st.write("Bar Chart - Total Crimes Each Year")
fig_bar = px.bar(crime_df, x="YEAR", y="TOTAL IPC CRIMES", title="Total Crimes Each Year")
st.plotly_chart(fig_bar, use_container_width=True)

# Pie chart for the distribution of selected crimes in the latest year with randomized data
latest_year_data = df[df["YEAR"] == df["YEAR"].max()]
st.write("Pie Chart - Distribution of Crimes (Latest Year)")
fig_pie = px.pie(
    latest_year_data,
    names=selected_crimes,
    title="Distribution of Crimes (Latest Year)",
    hole=0.4
)
st.plotly_chart(fig_pie, use_container_width=True)

# Area chart for the cumulative total crimes over the years with randomized data
st.write("Area Chart - Cumulative Total Crimes Over the Years")
crime_df["Cumulative Total Crimes"] = crime_df["TOTAL IPC CRIMES"].cumsum()
fig_area = px.area(crime_df, x="YEAR", y="Cumulative Total Crimes", title="Cumulative Total Crimes Over the Years")
st.plotly_chart(fig_area, use_container_width=True)

# Radar chart for the distribution of crimes by type with randomized data
st.write("Radar Chart - Distribution of Crimes by Type")
fig_radar = px.line_polar(latest_year_data, r=selected_crimes, theta=selected_crimes, line_close=True)
st.plotly_chart(fig_radar, use_container_width=True)

# Scatter plot for crime distribution based on latitude and longitude with randomized data
st.write("Scatter Plot - Crime Distribution Based on Latitude and Longitude (Random Data)")
fig_scatter_random = px.scatter_mapbox(
    df,
    lat="Location_Latitude",
    lon="Location_Longitude",
    color="TOTAL IPC CRIMES",
    size="TOTAL IPC CRIMES",
    hover_name="DISTRICT",
    title="Crime Distribution Based on Latitude and Longitude (Random Data)",
    mapbox_style="carto-positron",
    zoom=4,
    center={"lat": 20.5937, "lon": 78.9629},
)
st.plotly_chart(fig_scatter_random, use_container_width=True)

# Donut chart for the percentage of each crime type with randomized data
st.write("Donut Chart - Percentage of Each Crime Type")
fig_donut_random = px.pie(
    latest_year_data,
    names=selected_crimes,
    title="Percentage of Each Crime Type (Random Data)",
    hole=0.4
)
st.plotly_chart(fig_donut_random, use_container_width=True)

# Sunburst chart for hierarchical representation of crime data with randomized data
st.write("Sunburst Chart - Hierarchical Representation of Crime Data")
fig_sunburst_random = px.sunburst(
    latest_year_data,
    path=["STATE/UT", "DISTRICT", "TOTAL IPC CRIMES"],
    title="Hierarchical Representation of Crime Data (Random Data)"
)
st.plotly_chart(fig_sunburst_random, use_container_width=True)
