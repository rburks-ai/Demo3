import streamlit as st
import requests
import json
from datetime import datetime
from supabase import create_client, Client

# Replace with your actual Supabase credentials
SUPABASE_URL = "https://bfuenejemwghgohoxdww.supabase.co"
SUPABASE_KEY = "sb_publishable_HoiAWdS_bE3E_WID4CKb1A_L_GNXO3A"

# Initialize Supabase client
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="Weather Tracker", layout="wide")
st.title("🌤️ Weather Tracking App")

# OpenWeatherMap Free API
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

def get_weather_data(latitude, longitude):
    """Fetch weather data from Open-Meteo API (free, no key needed)"""
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto"
        }
        response = requests.get(WEATHER_API_URL, params=params)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching weather: {str(e)}")
        return None

def get_coordinates(city_name):
    """Get latitude/longitude from city name using Geocoding API"""
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
        response = requests.get(geo_url, params=params)
        data = response.json()
        
        if data.get("results"):
            result = data["results"][0]
            return result["latitude"], result["longitude"], result.get("name", city_name)
        return None, None, None
    except Exception as e:
        st.error(f"Error finding city: {str(e)}")
        return None, None, None

def get_weather_description(code):
    """Convert weather code to description"""
    weather_codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Foggy", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 80: "Slight showers",
        81: "Moderate showers", 82: "Violent showers", 85: "Slight snow showers",
        86: "Heavy snow showers", 95: "Thunderstorm", 96: "Thunderstorm with hail",
        99: "Thunderstorm with hail"
    }
    return weather_codes.get(code, "Unknown")

def load_weather_records():
    """Load all weather records from Supabase"""
    try:
        response = supabase.table("weather_records").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error loading records: {str(e)}")
        return []

def save_weather_record(record):
    """Save weather record to Supabase"""
    try:
        response = supabase.table("weather_records").insert(record).execute()
        return True
    except Exception as e:
        st.error(f"Error saving record: {str(e)}")
        return False

def delete_weather_record(record_id):
    """Delete weather record from Supabase"""
    try:
        supabase.table("weather_records").delete().eq("id", record_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting record: {str(e)}")
        return False

# Tabs
tab1, tab2, tab3 = st.tabs(["Weather Search", "Weather Logs", "Analytics"])

# Tab 1: Weather Search
with tab1:
    st.subheader("🔍 Search Weather by City")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        city_input = st.text_input("Enter city name", placeholder="New York, London, Tokyo...")
    
    with col2:
        search_btn = st.button("Search", use_container_width=True)
    
    if search_btn and city_input:
        with st.spinner("Fetching weather data..."):
            lat, lon, city_name = get_coordinates(city_input)
            
            if lat and lon:
                weather_data = get_weather_data(lat, lon)
                
                if weather_data:
                    current = weather_data.get("current", {})
                    
                    # Display weather info
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Temperature", f"{current.get('temperature_2m', 'N/A')}°C")
                    with col2:
                        st.metric("Humidity", f"{current.get('relative_humidity_2m', 'N/A')}%")
                    with col3:
                        st.metric("Wind Speed", f"{current.get('wind_speed_10m', 'N/A')} km/h")
                    with col4:
                        weather_desc = get_weather_description(current.get("weather_code", 0))
                        st.metric("Condition", weather_desc)
                    
                    st.divider()
                    
                    # Form to save weather record
                    st.subheader("💾 Save This Weather Record")
                    
                    with st.form("weather_form"):
                        notes = st.text_area("Add notes about this weather", placeholder="E.g., Good day for outdoor activities")
                        mood = st.selectbox("How's the weather affecting you?", ["Great", "Good", "Okay", "Bad", "Terrible"])
                        activity = st.text_input("What are you doing?", placeholder="E.g., Jogging, Working, Relaxing")
                        
                        submit = st.form_submit_button("Save Record", use_container_width=True)
                        
                        if submit:
                            new_record = {
                                "city": city_name,
                                "latitude": lat,
                                "longitude": lon,
                                "temperature": current.get('temperature_2m'),
                                "humidity": current.get('relative_humidity_2m'),
                                "wind_speed": current.get('wind_speed_10m'),
                                "condition": get_weather_description(current.get("weather_code", 0)),
                                "notes": notes,
                                "mood": mood,
                                "activity": activity,
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            if save_weather_record(new_record):
                                st.success(f"✅ Weather record for {city_name} saved successfully!")
                            else:
                                st.error("Failed to save record")
            else:
                st.error(f"City '{city_input}' not found. Try again!")

# Tab 2: Weather Logs
with tab2:
    st.subheader("📋 Your Weather Records")
    
    records = load_weather_records()
    
    if records:
        # Display stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(records))
        with col2:
            avg_temp = sum(r.get("temperature", 0) for r in records if r.get("temperature")) / max(len([r for r in records if r.get("temperature")]), 1)
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
        with col3:
            mood_counts = {}
            for r in records:
                mood = r.get("mood", "Unknown")
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
            most_common_mood = max(mood_counts, key=mood_counts.get) if mood_counts else "N/A"
            st.metric("Most Common Mood", most_common_mood)
        
        st.divider()
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            selected_city = st.selectbox(
                "Filter by city",
                ["All"] + list(set(r.get("city", "Unknown") for r in records)),
                key="city_filter"
            )
        
        with col2:
            selected_mood = st.selectbox(
                "Filter by mood",
                ["All"] + list(set(r.get("mood", "Unknown") for r in records)),
                key="mood_filter"
            )
        
        # Apply filters
        filtered_records = records
        if selected_city != "All":
            filtered_records = [r for r in filtered_records if r.get("city") == selected_city]
        if selected_mood != "All":
            filtered_records = [r for r in filtered_records if r.get("mood") == selected_mood]
        
        # Display filtered records
        for record in reversed(filtered_records):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{record.get('city', 'Unknown')}** - {record.get('condition', 'N/A')}")
                    st.write(f"🌡️ {record.get('temperature')}°C | 💨 {record.get('wind_speed')} km/h | 💧 {record.get('humidity')}%")
                    st.write(f"😊 Mood: **{record.get('mood')}** | 🎯 Activity: {record.get('activity', 'N/A')}")
                    if record.get('notes'):
                        st.write(f"📝 {record.get('notes')}")
                    st.caption(datetime.fromisoformat(record.get('timestamp')).strftime("%Y-%m-%d %H:%M"))
                
                with col2:
                    if st.button("Delete", key=f"del_{record.get('id')}", use_container_width=True):
                        if delete_weather_record(record.get('id')):
                            st.success("Deleted!")
                            st.rerun()
    else:
        st.info("No weather records yet. Search for a city and save a record!")

# Tab 3: Analytics
with tab3:
    st.subheader("📊 Weather Analytics")
    
    records = load_weather_records()
    
    if records:
        # Temperature over time
        st.write("**Temperature Trend**")
        temps = [r.get("temperature", 0) for r in records]
        st.line_chart(temps)
        
        # Mood distribution
        st.write("**Mood Distribution**")
        mood_counts = {}
        for r in records:
            mood = r.get("mood", "Unknown")
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        st.bar_chart(mood_counts)
        
        # Weather conditions
        st.write("**Recorded Conditions**")
        condition_counts = {}
        for r in records:
            condition = r.get("condition", "Unknown")
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
        
        st.bar_chart(condition_counts)
    else:
        st.info("No data to analyze yet!")
