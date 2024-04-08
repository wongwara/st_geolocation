import streamlit as st
import folium 
import pandas as pd
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

yellow_pages = pd.read_csv('yellow_pages_pharmacy_df.csv') 

# page setup
st.set_page_config(
    page_title="Oversea Student Healthcare Find Nearest Pharmacies",
    page_icon="🤗💬"
)

st.title('Oversea Student Healthcare Find Nearest Pharmacies')
st.markdown('Welcome to New South Wales Nearest Pharmacies finding!, We will need you to provide your current latitude and longitude.')
st.markdown('Once you provide the latitude and longitude, we will find the nearest pharmacies for you. You can find your current location from [here](https://www.gps-coordinates.net/my-location)')

# st.title("Streamlit Geolocation")

# try:
#     loc_string = streamlit_geolocation()
# except:
#     print("error")

# if loc_string is not None:
#     st.write(f"{loc_string}")

def get_user_location():
    st.text("Hello")
    if st.button("Get Location"):
        location = streamlit_geolocation()
        st.write(location)
        latitude = location.get('latitude')
        longitude = location.get('longitude')
        if latitude is not None and longitude is not None:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                return latitude, longitude
            except ValueError:
                st.error("Latitude or longitude value is not a valid number.")
        else:
            st.error("Latitude or longitude value is missing.")

    
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
    user_location = get_user_location()
    if user_location:
        try:
            nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages, top_n=10)
            if nearest_pharmacies:
                # Create a Folium map
                map_center = user_location
                m = folium.Map(location=map_center, zoom_start=15)

                # Create a MarkerCluster
                marker_cluster = MarkerCluster().add_to(m)

                # Add markers for user location and nearest pharmacies
                folium.Marker(location=map_center, popup="Your Location", icon=folium.Icon(color="green")).add_to(m)
                for pharmacy, distance in nearest_pharmacies:
                    popup_text = f"{pharmacy['pharmacy_name']}<br>Distance: {distance:.2f} km"
                    folium.Marker(location=(pharmacy['latitude'], pharmacy['longitude']), popup=popup_text).add_to(marker_cluster)

                # Change the color of the nearest pharmacy marker to red
                nearest_pharmacy_location = (nearest_pharmacies[0][0]['latitude'], nearest_pharmacies[0][0]['longitude'])
                folium.Marker(location=nearest_pharmacy_location, popup="Nearest Pharmacy", icon=folium.Icon(color="red")).add_to(m)

                # Display the map
                folium_static(m)
                nearest_pharmacies_df = pd.DataFrame(
                [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
                columns=['Pharmacy Name', 'Distance (km)']
            )
                st.subheader("Top 10 Nearest Pharmacies:")
                st.table(nearest_pharmacies_df)
                # for i, (pharmacy, distance) in enumerate(nearest_pharmacies, start=1):
                #     st.write(f"#{i}: {pharmacy['pharmacy_name']} - Distance: {distance:.2f} km")

            else:
                st.error("No pharmacies found.")
        except ValueError:
            st.error("Invalid input format. Please provide latitude and longitude in the format 'latitude, longitude'.")

if __name__ == "__main__":
    main()
