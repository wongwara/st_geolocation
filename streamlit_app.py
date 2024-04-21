import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from streamlit_chat import message  # For chatbot-like interaction

# Load your pharmacy data (example file path)
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

# Main Streamlit function
def main():
    st.title("Streamlit Chat")
    greeting = "Hi, how can I help you? Choose from menu items Diagnosis, OSHC, or Pharmacy Location."

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

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle menu selection
    if not st.session_state.menu_choice:
        menu_choice = st.selectbox("Select a menu item:", ["Diagnosis", "OSHC", "Pharmacy Location"])
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            st.experimental_rerun()  # Re-run to update the menu choice

    # Check if a menu item is selected and ask for the user input
    if st.session_state.menu_choice:
        if not st.session_state.showSelect:
            with st.chat_message("assistant"):
                st.markdown(f"OK {st.session_state.menu_choice}")
            st.session_state.showSelect = True

        # Get user input
        user_input = st.chat_input("What's up?")

        if user_input:
            # Display user input in the chat message
            with st.chat_message("user"):
                st.markdown(user_input)

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
                # Ask for the address
                with st.chat_message("assistant"):
                    st.markdown("Please enter your address:")
        
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
                        st.subheader("Top 10 Nearest Pharmacies:")
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
