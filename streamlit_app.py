import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static
from streamlit_chat import message  # Use for chatbot-like interaction

# Load pharmacy data
yellow_pages = pd.read_csv('yellow_pages_pharmacy_df.csv') 

# Initialize chatbot interface
if 'conversation' not in st.session_state:
    st.session_state['conversation'] = []

# Function to get the user location based on input
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

# Function to find nearest pharmacies based on a user location
def find_nearest_pharmacies(user_location, pharmacies, top_n=10):
    nearest_pharmacies = []
    distances = []
    for _, pharmacy in pharmacies.iterrows():
        try:
            latitude = float(pharmacy['latitude'])
            longitude = float(pharmacy['longitude'])
            pharmacy_location = (latitude, longitude)
            distance = geodesic(user_location, pharmacy_location).kilometers
            distances.append((pharmacy, distance))
        except ValueError:
            continue
    
    sorted_distances = sorted(distances, key=lambda x: x[1])
    return sorted_distances[:top_n]

# Function to create Folium map with nearest pharmacies
def create_pharmacy_map(user_location, nearest_pharmacies):
    m = folium.Map(location=user_location, zoom_start=14)
    marker_cluster = MarkerCluster().add_to(m)

    folium.Marker(
        location=user_location,
        popup="Your Location",
        icon=folium.Icon(color="green"),
    ).add_to(marker_cluster)

    for pharmacy, distance in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']} - Distance: {distance:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            popup=popup_text,
            icon=folium.Icon(color="blue"),
        ).add_to(marker_cluster)

    nearest_pharmacy = nearest_pharmacies[0][0]
    nearest_pharmacy_location = (
        nearest_pharmacy['latitude'],
        nearest_pharmacy['longitude']
    )
    folium.Marker(
        location=nearest_pharmacy_location,
        popup=f"Nearest Pharmacy: {nearest_pharmacy['pharmacy_name']}",
        icon=folium.Icon(color="red"),
    ).add_to(marker_cluster)

    return m

# Streamlit chatbot interface
st.title("Pharmacy Finder Chatbot")
st.markdown("Welcome! I can help you find the nearest pharmacies in New South Wales. Please enter your current address to begin.")

user_input = st.text_input("You:", key="user_input")  # Get user input

if st.button("Send"):
    if user_input:
        # Add user input to the conversation
        st.session_state['conversation'].append({"type": "user", "text": user_input})

        # Process user input
        user_latitude, user_longitude = get_user_location(user_input)
        if user_latitude is not None and user_longitude is not None:
            user_location = (user_latitude, user_longitude)
            nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages, top_n=10)

            if nearest_pharmacies:
                # Create and display the map with nearest pharmacies
                map_object = create_pharmacy_map(user_location, nearest_pharmacies)
                folium_static(map_object)

                # Display a table with nearest pharmacies
                nearest_pharmacies_df = pd.DataFrame(
                    [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
                    columns=['Pharmacy Name', 'Distance (km)']
                )
                st.subheader("Top 10 Nearest Pharmacies:")
                st.table(nearest_pharmacies_df)

                # Add chatbot response
                st.session_state['conversation'].append({"type": "bot", "text": "Here are the nearest pharmacies and their distances."})
            else:
                # Handle case where no pharmacies are found
                st.error("No pharmacies found near your location.")
                st.session_state['conversation'].append({"type": "bot", "text": "No pharmacies were found near your location."})
        else:
            # Handle invalid user location
            st.warning("Address not found. Please check and try again.")
            st.session_state['conversation'].append({"type": "bot", "text": "I couldn't find your address. Please try again."})

# Display the chatbot conversation
for msg in st.session_state['conversation']:
    if msg["type"] == "user":
        message(msg["text"], is_user=True)
    else:
        message(msg["text"], is_user=False)
