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
        ).add_to(marker_cluster)

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
    st.title(" 🤖 Oversea Student Health Chatbot")
    greeting = "Hi, how can I help you? "
    option_to_choose = " Choose from menu items Diagnosis, OSHC, or Pharmacy Location."
    information = 'This application is demo application for chatbot. You can ask for the Pharmacy Location.'

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize menu choice
    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = None
    
    if "showSelect" not in st.session_state:
        st.session_state.showSelect = False

    # Display initial message
    with st.chat_message("assistant"):
        st.markdown(greeting)
        st.markdown(option_to_choose)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle menu selection
    if not st.session_state.menu_choice:
        menu_choice = st.selectbox("Select a menu item:", ["Diagnosis", "OSHC", "Pharmacy Location"])
        st.markdown(information)
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            st.experimental_rerun()  # Re-run to update the menu choice

    # Check if a menu item is selected and ask for the user input
    if st.session_state.menu_choice:
        if not st.session_state.showSelect:
            with st.chat_message("assistant"):
                st.markdown(f"OK You selected {st.session_state.menu_choice}")
                if st.session_state.menu_choice == "Pharmacy Location":
                    st.markdown("for the Pharmacy Location - Please enter your address:")
                else:
                    st.markdown("Please wait for the update version in the future.")
            st.session_state.showSelect = True

        # Get user input
        user_input = st.chat_input("What's up? You can type 'quit' to restart.")

        if user_input:

            if user_input.lower() == "quit":
                # Reset the session state if "quit" is entered
                st.session_state.messages = []
                st.session_state.menu_choice = None
                st.session_state.showSelect = False
                with st.chat_message("assistant"):
                    st.markdown("Thanks for using the chatbot! Restarting...")
                st.experimental_rerun()  # Re-run after reset

            # Handle Pharmacy Location logic
            if st.session_state.menu_choice == "Pharmacy Location":
                with st.chat_message("assistant"):
                    st.markdown("Please enter your address:")
                with st.chat_message("user"):
                    st.markdown(user_input)
                # Ask for the address
                with st.chat_message("assistant"):
                    st.markdown("Here's the map with the nearest pharmacies and their distances:")
        
                # Get the user's location from the address
                    user_lat, user_lon = get_user_location(user_input)
                if user_lat and user_lon:
                    user_location = (user_lat, user_lon)

                    # Find the nearest pharmacies
                    nearest_pharmacies = find_nearest_pharmacies((user_location), yellow_pages, top_n=10)

                    if nearest_pharmacies:
                        # Create the map with nearest pharmacies
                        map_object = create_pharmacy_map(user_location, nearest_pharmacies)
                        folium_static(map_object)

                        # Display the top 10 nearest pharmacies in a table
                        nearest_pharmacies_df = pd.DataFrame(
                            [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
                            columns=['Pharmacy Name', 'Distance (km)']
                        )
                        with st.chat_message("assistant"):
                            st.markdown("Top 10 Nearest Pharmacies:")
                            st.table(nearest_pharmacies_df)

                        # Add the response to the chat history
                        st.session_state.messages.append(
                            {"role": "assistant", "content": "Here's the map with the nearest pharmacies and their distances."}
                        )
                    else:
                        st.error("No pharmacies found near your location.")
                        st.session_state.messages.append(
                            {"role": "assistant", "content": "No pharmacies found near your location."}
                        )
                else:
                    st.warning("Address not found. Please check and try again.")
                    st.session_state.messages.append(
                            {"role": "assistant", "content": "Address not found. Please try again."}
                    )

# Run the Streamlit app
if __name__ == "__main__":
    main()
