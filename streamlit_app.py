import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from streamlit_chat import message  # Used for chatbot-like interaction

# Load your pharmacy data (ensure the data exists)
yellow_pages = pd.read_csv('yellow_pages_pharmacy_df.csv') 

# Create a chatbot interface
if 'conversation' not in st.session_state:
    st.session_state['conversation'] = []

# Define a function to get user latitude and longitude from an address
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude  # Return the latitude and longitude
    else:
        return None, None

# Define a function to find the nearest pharmacies based on user location
def find_nearest_pharmacies(user_location, pharmacies, top_n=10):
    distances = []
    for _, pharmacy in pharmacies.iterrows():
        try:
            latitude = float(pharmacy['latitude'])
            longitude = float(pharmacy['longitude'])
            pharmacy_location = (latitude, longitude)
            distance = geodesic(user_location, pharmacy_location).kilometers
            distances.append((pharmacy, distance))
        except (ValueError, KeyError):
            continue  # Skip if latitude or longitude is invalid
    
    # Sort pharmacies by distance and return top N
    sorted_distances = sorted(distances, key=lambda x: x[1])
    return sorted_distances[:top_n]

# Create a Folium map with the nearest pharmacies
def create_pharmacy_map(user_location, nearest_pharmacies):
    m = folium.Map(location=user_location, zoom_start=14)
    marker_cluster = MarkerCluster().add_to(m)

    # Add a marker for the user's location
    folium.Marker(
        location=user_location,
        popup="Your Location",
        icon=folium.Icon(color="green"),
    ).add_to(marker_cluster)

    # Add markers for nearest pharmacies
    for pharmacy, distance in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']} - Distance: {distance:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            popup=popup_text,
            icon=folium.Icon(color="blue"),
        ).add_to(marker_cluster)

    # Highlight the nearest pharmacy
    nearest_pharmacy = nearest_pharmacies[0][0]
    folium.Marker(
        location=(nearest_pharmacy['latitude'], nearest_pharmacy['longitude']),
        popup=f"Nearest Pharmacy: {nearest_pharmacy['pharmacy_name']}",
        icon=folium.Icon(color="red"),
    ).add_to(marker_cluster)

    return m

# Chatbot interaction in Streamlit
st.title("Pharmacy Finder Chatbot")
st.markdown("Welcome! I can help you find the nearest pharmacies in New South Wales.")

# Bot initiates the conversation by asking for the address
if len(st.session_state['conversation']) == 0:
    st.session_state['conversation'].append({"type": "bot", "text": "Please enter your address to find the nearest pharmacies."})

# Get user input for the chatbot
user_input = st.text_input("You:", key="user_input")  # Chat-like input field

if st.button("Send"):  # When the user sends a message
    if user_input:
        st.session_state['conversation'].append({"type": "user", "text": user_input})  # Add to conversation

        # Get the user's location from the address
        user_latitude, user_longitude = get_user_location(user_input)
        if user_latitude is not None and user_longitude is not None:
            user_location = (user_latitude, user_longitude)

            # Find the nearest pharmacies
            nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages, top_n=10)

            if nearest_pharmacies:
                # Create the map with nearest pharmacies
                map_object = create_pharmacy_map(user_location, nearest_pharmacies)
                folium_static(map_object)

                # Display a table with nearest pharmacies
                nearest_pharmacies_df = pd.DataFrame(
                    [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
                    columns=['Pharmacy Name', 'Distance (km)']
                )
                st.subheader("Top 10 Nearest Pharmacies:")
                st.table(nearest_pharmacies_df)  # Show the table

                # Add chatbot response
                st.session_state['conversation'].append({"type": "bot", "text": "Here is the map with the nearest pharmacies and their distances."})
            else:
                st.error("No pharmacies found near your location.")
                st.session_state['conversation'].append({"type": "bot", "text": "No pharmacies were found near your location."})
        else:
            st.warning("Address not found. Please check and try again.")
            st.session_state['conversation'].append({"type": "bot", "text": "I couldn't find your address. Please check and try again."})

# Display the chatbot conversation with messages
for msg in st.session_state['conversation']:
    if msg["type"] == "user":
        message(msg["text"], is_user=True)  # User message
    else:
        message(msg["text"], is_user=False)  # Bot message
