import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from streamlit_chat import message  # For chatbot-like interaction

chat_history = []

# Load your pharmacy data
yellow_pages = pd.read_csv('yellow_pages_pharmacy_df.csv')

# Define the function to get user latitude and longitude from an address
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
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
        icon=folium.Icon(color="orange"),
    ).add_to(m)

    # Add markers for nearest pharmacies with distance and name in the popup text
    for pharmacy, distance in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']} - Distance: {distance:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            icon=folium.Icon(color="blue"),
            popup=popup_text,
        ).add_to(m)

    # Highlight the nearest pharmacy with a red icon and a popup with distance and name
    nearest_pharmacy, nearest_distance = nearest_pharmacies[0]
    nearest_pharmacy_location = (nearest_pharmacy['latitude'], nearest_pharmacy['longitude'])
    folium.Marker(
        location=nearest_pharmacy_location,
        popup=f"Nearest Pharmacy: {nearest_pharmacy['pharmacy_name']} - Distance: {nearest_distance:.2f} km",
        icon=folium.Icon(color="red"),
    ).add_to(m)

    return m

# Main Streamlit function
def main():
    st.title("🤖 Oversea Student Health Chatbot")

    # Initialize chat history and menu choice
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = None

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle menu selection
    if st.session_state.menu_choice is None:
        menu_choice = st.selectbox("Select a menu item:", ["Diagnosis", "OSHC", "Pharmacy Location"])
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            st.experimental_rerun()  # Re-run to update the menu choice

    # Display assistant message after selecting Pharmacy Location
    if st.session_state.menu_choice == "Pharmacy Location":
        # Ask for the address
        with st.chat_message("assistant"):
            st.markdown("Please enter your address:")
        
    user_input = st.chat_input("Enter your address or type 'quit' to restart:")

    # Check if user input is not empty or None
    if user_input.lower() == "quit":
            # Reset the session state if "quit" is entered
            st.session_state.messages = []
            st.session_state.menu_choice = None
            st.experimental_rerun()  # Re-run after reset

    elif user_input:
            # Add user input to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get the user's location from the address
            user_lat, user_lon = get_user_location(user_input)
            
            if user_lat and user_lon:
                user_location = (user_lat, user_lon)

                # Find the nearest pharmacies
                nearest_pharmacies = find_nearest_pharmacies((user_location), yellow_pages, top_n=10)

                # Set a maximum distance in km
                max_distance_km = 10.0

                #  Filter pharmacies by the maximum distance
                filtered_pharmacies = [
                    (pharmacy, distance) for pharmacy, distance in nearest_pharmacies if distance <= max_distance_km
                ]

                if filtered_pharmacies is None:
                    response = "Here's the map with the nearest pharmacies and their distances."

                    # Create the map with filtered pharmacies
                    map_object = create_pharmacy_map(user_location, filtered_pharmacies)
                    folium_static(map_object)

                    # Display the filtered pharmacies in a table
                    nearest_pharmacies_df = pd.DataFrame(
                        [
                            (pharmacy["pharmacy_name"], f"{distance:.2f} km")
                            for pharmacy, distance in filtered_pharmacies
                        ],
                        columns=["Pharmacy Name", "Distance (km)"],
                    )
                    st.subheader("Nearest Pharmacies within 10 km:")
                    st.table(nearest_pharmacies_df)

                    # Display the response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(response)

                else:
                    st.error("No pharmacies found within 10 km of your location.")
                    response = "No pharmacies found within 10 km of your location."

                    # Display bot response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(response)

            else:
                st.warning("Address not found. Please check and try again.")
                response = "Address not found. Please try again."
                
                # Display warning message in chat container
                with st.chat_message("assistant"):
                    st.markdown(response)

    # Handle chat history update
    st.session_state.messages.append({"role": "assistant", "content": response})

# Run the Streamlit app
if __name__ == "__main__":
    main()
