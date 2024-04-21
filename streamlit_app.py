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

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.chat_message("user"):
    st.write("Hello 👋")

with st.chat_message("assistant"):
    st.write("Hello human")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
# Initialize conversation state
if 'conversation' not in st.session_state:
    # Start with a welcome message from the chatbot
    st.session_state['conversation'] = [{"type": "bot", "text": "Hello! Please enter your address, and I'll find the nearest pharmacies for you."}]

# Define the function to get user latitude and longitude from an address
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude  # Return lat/long
    else:
        return None, None

# Define the function to find the nearest pharmacies based on user location
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

# Function to create a Folium map with nearest pharmacies
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
            icon=folium.Icon(color="blue"),
        ).add_to(marker_cluster)

    # Highlight the nearest pharmacy with a red icon
    nearest_pharmacy = nearest_pharmacies[0][0]
    folium.Marker(
        location=(nearest_pharmacy['latitude'], nearest_pharmacy['longitude']),
        popup=f"Nearest Pharmacy: {nearest_pharmacy['pharmacy_name']}",
        icon=folium.Icon(color="red"),
    ).add_to(m)

    return m

# Start the chatbot conversation with a message from the bot
st.title("Pharmacy Finder Chatbot")
st.subheader("Enter your address to find the nearest pharmacies.")
st.markdown("You can also ask questions or provide feedback in the chat.")


# Get user input for the chatbot
user_input = st.text_input("Type your response here:", key="user_input")  # Chat-like input field

if st.button("Send", key="send_button"):  # Ensure unique key for the button
    if user_input:
        st.session_state['conversation'].append({"type": "user", "text": user_input})

        # Get the user's location from the address
        user_latitude, user_longitude = get_user_location(user_input)
        if user_latitude and user_longitude:
            user_location = (user_latitude, user_longitude)

            # Find the nearest pharmacies
            nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages, top_n=10)

            if nearest_pharmacies:
                # Create the map with nearest pharmacies
                map_object = create_pharmacy_map(user_location, nearest_pharmacies)
                folium_static(map_object)

                # Display the top 10 nearest pharmacies in a table
                nearest_pharmacies_df = pd.DataFrame(
                    [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
                    columns=['Pharmacy Name', 'Distance (km)']
                )
                st.subheader("Top 10 Nearest Pharmacies:")
                st.table(nearest_pharmacies_df)

                # Add a chatbot response
                st.session_state['conversation'].append({"type": "bot", "text": "Here's the map with the nearest pharmacies and their distances."})
            else:
                st.error("No pharmacies found near your location.")
                st.session_state['conversation'].append({"type": "bot", "text": "No pharmacies were found near your location."})
        else:
            st.warning("Address not found. Please check and try again.")
            st.session_state['conversation'].append({"type": "bot", "text": "I couldn't find your address. Please check and try again."})

# Display the chatbot conversation with messages, each with a unique key
for i, msg in enumerate(st.session_state['conversation']):
    if msg["type"] == "user":
        message(msg["text"], is_user=True, key=f"user_{i}")  # User message with unique key
    else:
        message(msg["text"], is_user=False, key=f"bot_{i}")  # Bot message with unique key
