import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

# Function to get user latitude and longitude from an address
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

# Function to find the nearest pharmacies based on user location
def find_nearest_pharmacies(user_location, pharmacies):
    pharmacies["distance"] = pharmacies.apply(
        lambda row: geodesic(user_location, (row["latitude"], row["longitude"])).kilometers,
        axis=1
    )
    # Sort and get top 10 nearest pharmacies
    return pharmacies.sort_values("distance").head(10).to_dict(orient="records")

# Function to create a Folium map with nearest pharmacies
def create_pharmacy_map(user_location, nearest_pharmacies):
    m = folium.Map(location=user_location, zoom_start=15)
    marker_cluster = MarkerCluster().add_to(m)

    # Add marker for user location
    folium.Marker(
        location=user_location,
        popup="Your Location",
        icon=folium.Icon(color="green"),
    ).add_to(m)

    # Add markers for nearest pharmacies
    for pharmacy in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']}<br>Distance: {pharmacy['distance']:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            popup=popup_text,
            icon=folium.Icon(color="red"),
        ).add_to(marker_cluster)

    folium_static(m)

# Load your pharmacy data (example file path)
yellow_pages = pd.read_csv("yellow_pages_pharmacy_df.csv")

# Initialize the chat history
chat_history = []

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

    # Handle user input
    if not st.session_state.menu_choice:
        menu_choice = st.selectbox("Select a menu item:", ["Diagnosis", "OSHC", "Pharmacy Location"])
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            st.experimental_rerun()  # Re-run to update the menu choice

    if st.session_state.menu_choice:
        if not st.session_state.showSelect:
            with st.chat_message("assistant"):
                st.markdown(f"OK {st.session_state.menu_choice}")
            st.session_state.showSelect = True

        # Get user input
        user_input = st.chat_input("What's up?")

        if user_input:
            # Display user input in chat message
            with st.chat_message("user"):
                st.markdown(user_input)

            # Handle "quit" command
            if user_input.lower() == "quit":
                # Reset the session state
                st.session_state.messages = []
                st.session_state.menu_choice = None
                st.session_state.showSelect = False
                # Thank the user and re-run
                with st.chat_message("assistant"):
                    st.markdown("Thanks for using the chatbot! Restarting...")
                st.experimental_rerun()  # Re-run the app after resetting

            # Handle Pharmacy Location logic
            elif st.session_state.menu_choice == "Pharmacy Location":
                # Ask for the address
                with st.chat_message("assistant"):
                    st.markdown("Please enter your address:")
                if user_input:
                    # Get the user's latitude and longitude
                    lat, lon = get_user_location(user_input)
                    if lat is not None and lon is not None:
                        # Find nearest pharmacies
                        nearest_pharmacies = find_nearest_pharmacies((lat, lon), yellow_pages)
                        with st.chat_message("assistant"):
                            st.markdown("Here are the nearest pharmacies:")
                            st.write(nearest_pharmacies)

                        # Display a map with nearest pharmacies
                        create_pharmacy_map((lat, lon), nearest_pharmacies)
                    else:
                        with st.chat_message("assistant"):
                            st.markdown("Address not found. Please try again.")


if __name__ == "__main__":
    main()
