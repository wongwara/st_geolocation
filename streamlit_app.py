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
    for pharmacy in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']}<br>Distance: {pharmacy['distance']:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            popup=popup_text,
            icon=folium.Icon(color="blue")
        ).add_to(marker_cluster)

    folium_static(m)

# Main function
def main():
    st.title("Streamlit Chat")

    # Initialize chat history and session state
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
            st.rerun()

    # Process user input
    if st.session_state.menu_choice == "Pharmacy Location":
        if "user_location" not in st.session_state:
            # Ask for user input to get their location
            user_input = st.chat_input("Please enter your address:", key="user_address")
            if user_input:
                latitude, longitude = get_user_location(user_input)
                if latitude is not None and longitude is not None:
                    st.session_state["user_location"] = (latitude, longitude)
                    nearest_pharmacies = find_nearest_pharmacies(st.session_state["user_location"], yellow_pages)
                    create_pharmacy_map(st.session_state["user_location"], nearest_pharmacies)

                    response = "Here are the nearest pharmacies:"
                    for i, pharmacy in enumerate(nearest_pharmacies, 1):
                        response += f"\n{i}. {pharmacy['pharmacy_name']} - Distance: {pharmacy['distance']:.2f} km"

                    # Store and display response
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.markdown(response)
                else:
                    response = "Sorry, could not find the location. Please try again."
                    with st.chat_message("assistant"):
                        st.markdown(response)
        else:
            st.write("Pharmacy Location menu chosen. Please provide an address.")

    elif st.session_state.menu_choice == "Diagnosis":
        st.write("Diagnosis menu chosen.")
    
    elif st.session_state.menu_choice == "OSHC":
        st.write("OSHC menu chosen.")

    # If user enters "quit", clear the session state and restart
    if user_input == "quit":
        st.session_state.clear()
        st.experimental_rerun()

if __name__ == "__main__":
    main()
