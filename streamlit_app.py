import streamlit as st
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from streamlit_chat import message  # For chatbot-like interaction

# Load your pharmacy data
yellow_pages = pd.read_csv("yellow_pages_pharmacy_df.csv")

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
        icon=folium.Icon(color="green")
    ).add_to(m)

    # Add markers for nearest pharmacies
    for pharmacy in nearest pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']}<br>Distance: {pharmacy['distance']:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            popup=popup_text,
            icon=folium.Icon(color="blue")
        ).add_to(marker_cluster)

    folium_static(m)

def main():
    st.title("Streamlit Chat")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = None

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle menu choice
    if st.session_state.menu_choice is None:
        menu_choice = st.selectbox("Select a menu item:", options=["Diagnosis", "OSHC", "Pharmacy Location"], key="menu_choice_select")
        if st.button("Submit", key="menu_submit"):
            st.session_state.menu_choice = menu_choice
            st.experimental_rerun()

    # Process user input
    user_input = None  # Initialize user_input to avoid referencing issues

    if st.session_state.menu_choice is not None:
        user_input = st.chat_input("What's up?")  # Create a unique key or condition

    # If user_input is defined, process it
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        if user_input.lower() == "quit":
            # Clear session state on quit
            st.session_state.clear()
            st.experimental_rerun()

        elif st.session_state.menu_choice == "OSHC":
            st.write("OSHC selected")

        elif st.session_state.menu_choice == "Diagnosis":
            st.write("Diagnosis selected")

        elif st.session_state.menu_choice == "Pharmacy Location":
            # Request user location input
            user_input = st.chat_input("Please enter your address:")
            if user_input:
                latitude, longitude = get_user_location(user_input)
                if latitude and longitude:
                    user_location = (latitude, longitude)
                    nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages)
                    create_pharmacy_map(user_location, nearest_pharmacies)

                    response = "Here are the nearest pharmacies:"
                    for i, pharmacy in enumerate(nearest_pharmacies, 1):
                        response += f"\n{i}. {pharmacy['pharmacy_name']} - Distance: {pharmacy['distance']:.2f} km"

                    st.session_state.messages.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.markdown(response)
                else:
                    response = "Sorry, could not find the location. Please try again."
                    st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
