import requests
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
import time

# Function to get data from the Flask API
def get_data():
    try:
        response = requests.get('http://127.0.0.1:8000/Home/Temperature', timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
        return {}

# Main function to display data and charts
def main():
    st.title("Environmental Dashboard")

    # Navigation buttons
    if st.button('Go to AQI Tips'):
        st.session_state.page = 'tips'
        st.experimental_rerun()
    
    data = get_data()

    if data:
        temperature = data["Data"]["Temperature"]
        humidity = data["Data"]["Humidity"]
        aqi = data["Data"]["AQI"]
        smoke_level = data.get('smoke_level', 0)
        
        # Function to create frames for animation
        def create_frames(value, range_max):
            return [go.Frame(data=[go.Indicator(
                mode="gauge+number",
                value=val,
                gauge={'axis': {'range': [None, range_max]}}
            )], name=str(val)) for val in np.linspace(0, value, 50)]
        
        # Circular indicator for AQI with animation
        fig_aqi = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=aqi,
                title={'text': "AQI"},
                gauge={
                    'axis': {'range': [None, 500]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "green"},
                        {'range': [51, 100], 'color': "yellow"},
                        {'range': [101, 150], 'color': "orange"},
                        {'range': [151, 200], 'color': "red"},
                        {'range': [201, 300], 'color': "purple"},
                        {'range': [301, 500], 'color': "maroon"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': aqi
                    }
                }
            )
        )
        fig_aqi.frames = create_frames(aqi, 500)
        fig_aqi.update_layout(updatemenus=[{'buttons': [{'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'fromcurrent': True}],
                                                         'label': 'Update',
                                                         'method': 'animate'}]}])

        # Circular indicator for Humidity with animation
        fig_humidity = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=humidity,
                title={'text': "Humidity"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "blue"},
                    'steps': [
                        {'range': [0, 20], 'color': "lightblue"},
                        {'range': [20, 40], 'color': "blue"},
                        {'range': [40, 60], 'color': "green"},
                        {'range': [60, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': humidity
                    }
                }
            )
        )
        fig_humidity.frames = create_frames(humidity, 100)
        fig_humidity.update_layout(updatemenus=[{'buttons': [{'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'fromcurrent': True}],
                                                            'label': 'Update',
                                                            'method': 'animate'}]}])

        # Circular indicator for Temperature with animation
        fig_temperature = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=temperature,
                title={'text': "Temperature"},
                gauge={
                    'axis': {'range': [-50, 50]},
                    'bar': {'color': "red"},
                    'steps': [
                        {'range': [-50, -20], 'color': "blue"},
                        {'range': [-20, 0], 'color': "lightblue"},
                        {'range': [0, 20], 'color': "yellow"},
                        {'range': [20, 35], 'color': "orange"},
                        {'range': [35, 50], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': temperature
                    }
                }
            )
        )
        fig_temperature.frames = create_frames(temperature, 50)
        fig_temperature.update_layout(updatemenus=[{'buttons': [{'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'fromcurrent': True}],
                                                                'label': 'Update',
                                                                'method': 'animate'}]}])

        st.plotly_chart(fig_aqi, use_container_width=True)
        st.plotly_chart(fig_humidity, use_container_width=True)
        st.plotly_chart(fig_temperature, use_container_width=True)

        # Add AQI details
        st.subheader("AQI Details")
        if aqi <= 50:
            st.markdown("**Good (0-50):** Air quality is considered satisfactory, and air pollution poses little or no risk.")
        elif aqi <= 100:
            st.markdown("**Moderate (51-100):** Air quality is acceptable; however, for some pollutants, there may be a moderate health concern for a very small number of people who are unusually sensitive to air pollution.")
        elif aqi <= 150:
            st.markdown("**Unhealthy for Sensitive Groups (101-150):** Members of sensitive groups may experience health effects. The general public is not likely to be affected.")
        elif aqi <= 200:
            st.markdown("**Unhealthy (151-200):** Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.")
        elif aqi <= 300:
            st.markdown("**Very Unhealthy (201-300):** Health alert: everyone may experience more serious health effects.")
        else:
            st.markdown("**Hazardous (301-500):** Health warnings of emergency conditions. The entire population is more likely to be affected.")
    else:
        st.warning("No data available.")

# Function to display AQI tips
def aqi_tips():
    st.title("AQI Tips")

    # Navigation buttons
    if st.button('Go to Main Page'):
        st.session_state.page = 'main'
        st.experimental_rerun()

    st.subheader("Tips for Each AQI Range")
    st.markdown("""
    - **Good (0-50):** Enjoy your usual outdoor activities.
    - **Moderate (51-100):** Sensitive individuals should consider limiting prolonged outdoor exertion.
    - **Unhealthy for Sensitive Groups (101-150):** Sensitive groups should reduce prolonged or heavy exertion outdoors.
    - **Unhealthy (151-200):** Everyone should reduce prolonged or heavy exertion outdoors. Sensitive groups should avoid outdoor exertion.
    - **Very Unhealthy (201-300):** Avoid prolonged or heavy exertion. Move activities indoors or reschedule.
    - **Hazardous (301-500):** Everyone should avoid all physical activities outdoors. Remain indoors and keep activity levels low.
    """)

# Check for session state to determine which page to display
if 'page' not in st.session_state:
    st.session_state.page = 'main'

if st.session_state.page == 'main':
    main()
else:
    aqi_tips()

# Auto-refresh every 5 seconds
time.sleep(3)
st.rerun()
