import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from streamlit_chat import message  # For chatbot-like interaction

# Load your pharmacy data
yellow_pages = pd.read_csv('yellow_pages_pharmacy_df.csv')

# Initialize chat history if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []  # List of chat messages
    
# Define function to get user latitude and longitude from an address
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude  # Return lat/long
    else:
        return None, None
    
# Define function to find the nearest pharmacies based on user location
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

# Define function to create a Folium map with nearest pharmacies
def create_pharmacy_map(user_location, nearest_pharmacies):
    m = folium.Map(location=user_location, zoom_start=14)
    marker_cluster = MarkerCluster().add_to(m)

    # Add a marker for the user's location
    folium.Marker(
        location=user_location,
        popup="Your Location",
        icon=folium.Icon(color="green"),
    ).add_to(marker_cluster)

    # Add markers for the nearest pharmacies
    for pharmacy, distance in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']} - Distance: {distance:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            icon=folium.Icon(color="blue"),
        ).add_to(marker_cluster)

    return m

# Create a simple chatbot interaction
st.title("Pharmacy Finder Chatbot")

# Display previous chat messages
for msg in st.session_state.messages:
    if msg["type"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])  # Display user message
    elif msg["type"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])  # Display bot message

# User input for new message
user_input = st.text_input("You: ", key="user_input")  # Text input for user response

if st.button("Send"):  # Button to send the user message
    if user_input:  # If user has entered text
        # Store user message
        st.session_state.messages.append({
            "type": "user",
            "content": user_input
        })

        # Get the user's location from the address
        user_latitude, user_longitude = get_user_location(user_input)
        if user_latitude and user_longitude:
            user_location = (user_latitude, user_longitude)

            # Find the nearest pharmacies
            nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages, top_n=10)

            # Display response and map
            if nearest_pharmacies:
                # Add chatbot response
                st.session_state.messages.append({
                    "type": "assistant",
                    "content": "Here's the map with the nearest pharmacies and their distances."
                })

                # Create the map and display it
                map_object = create_pharmacy_map(user_location, nearest_pharmacies)
                folium_static(map_object)

                # Display the top 10 nearest pharmacies in a table
                nearest_pharmacies_df = pd.DataFrame(
                    [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
                    columns=['Pharmacy Name', 'Distance (km)']
                )
                st.subheader("Top 10 Nearest Pharmacies:")
                st.table(nearest_pharmacies_df)

            else:
                # No pharmacies found message
                st.session_state.messages.append({
                    "type": "assistant",
                    "content": "No pharmacies found near your location."
                })
        else:
            # Address not found message
            st.session_state.messages.append({
                "type": "assistant",
                "content": "Address not found. Please check and try again."
            })

# Display the updated chat conversation
for msg in st.session_state.messages:
    if msg["type"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])  # Display user message
    elif msg["type"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])  # Display bot message
