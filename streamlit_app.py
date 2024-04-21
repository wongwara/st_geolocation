import streamlit as st
import folium 
import pandas as pd
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim

yellow_pages = pd.read_csv('yellow_pages_pharmacy_df.csv') 

# page setup
st.set_page_config(
    page_title="Oversea Student Healthcare Find Nearest Pharmacies",
    page_icon="🤗💬"
)

st.title('Oversea Student Healthcare Find Nearest Pharmacies')
st.markdown('Welcome to New South Wales Nearest Pharmacies finding!, We will need you to provide your current latitude and longitude.')
st.markdown('Once you provide the latitude and longitude, we will find the nearest pharmacies for you. You can find your current location from [here](https://www.gps-coordinates.net/my-location)')

from geopy.geocoders import Nominatim

def get_user_location():
    user_input = st.text_input("Enter your address")  # Prompt user for address
    if st.button("Get Coordinates"):  # Button to trigger fetching location
        geolocator = Nominatim(user_agent="geo_locator")
        location = geolocator.geocode(user_input)  # Geocode the address
        if location:
            return location.latitude, location.longitude  # Return lat/long
        else:
            st.warning("Address not found. Please check and try again.")  # Display a warning
    return None

def find_nearest_pharmacies(user_location, pharmacies, top_n=10):
    nearest_pharmacies = []
    distances = []
    for idx, pharmacy in pharmacies.iterrows():
        try:
            latitude = float(pharmacy['latitude'])
            longitude = float(pharmacy['longitude'])
        except ValueError:
            continue  # Skip this pharmacy if latitude or longitude is not a valid float
        
        pharmacy_location = (latitude, longitude)
        distance = geodesic(user_location, pharmacy_location).kilometers
        distances.append((pharmacy, distance))
    
    # Sort distances by distance
    sorted_distances = sorted(distances, key=lambda x: x[1])
    
    # Get top N pharmacies
    for pharmacy, distance in sorted_distances[:top_n]:
        nearest_pharmacies.append((pharmacy, distance))
    
    return nearest_pharmacies

def main():
    st.title("Nearest Pharmacies Finder")  # App title
    user_location = get_user_location()
    if user_location:  # If valid user location is obtained
        nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages, top_n=10)  # Find nearest pharmacies

        if nearest_pharmacies:
            # Create a Folium map centered on the user's location
            m = folium.Map(location=user_location, zoom_start=14)
            marker_cluster = MarkerCluster().add_to(m)

            # Add a marker for the user's location
            folium.Marker(
                location=user_location,
                popup="Your Location",
                icon=folium.Icon(color="green"),
            ).add_to(m)

            # Add markers for the nearest pharmacies
            for pharmacy, distance in nearest_pharmacies:
                popup_text = f"{pharmacy['pharmacy_name']} - Distance: {distance:.2f} km"
                folium.Marker(
                    location=(pharmacy['latitude'], pharmacy['longitude']),
                    popup=popup_text,
                    icon=folium.Icon(color="blue"),
                ).add_to(marker_cluster)

            # Mark the nearest pharmacy with a red icon
            nearest_pharmacy = nearest_pharmacies[0][0]
            nearest_pharmacy_location = (
                nearest_pharmacy['latitude'],
                nearest_pharmacy['longitude']
            )
            folium.Marker(
                location=nearest_pharmacy_location,
                popup=f"Nearest Pharmacy: {nearest_pharmacy['pharmacy_name']}",
                icon=folium.Icon(color="red"),
            ).add_to(m)

            # Display the Folium map
            folium_static(m)

            # Display a table with the top 10 nearest pharmacies
            nearest_pharmacies_df = pd.DataFrame(
                [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
                columns=['Pharmacy Name', 'Distance (km)']
            )
            st.subheader("Top 10 Nearest Pharmacies:")
            st.table(nearest_pharmacies_df)  # Show the table

        else:
            st.error("No pharmacies found near your location.")  # If no pharmacies found

if __name__ == "__main__":
    main()

st.markdown('This app is created by Group 11')
