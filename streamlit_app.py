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
    if location and location.latitude and location.longitude:
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
    if not user_location:
        return  # Safely exit if user location is invalid

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
    
    # Display top 10 nearest pharmacies
    nearest_pharmacies_df = pd.DataFrame(
        [(pharmacy['pharmacy_name'], f"{pharmacy['distance']:.2f} km")],
        columns=['Pharmacy Name', 'Distance (km)']
    )
    st.subheader("Top 10 Nearest Pharmacies:")
    st.table(nearest_pharmacies_df)

def main():
    st.title("Streamlit Chat")
    
    # Initialize chat history if not already present
    if "messages" not in st.session_state:
        st.session_state.messages = [] 
    
    # Initialize menu choice and control state
    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = None
    
    if "showSelect" not in st.session_state:
        st.session_state.showSelect = True
    
    # Initial chatbot greeting
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("Hi, how can I help you? Choose from menu items Diagnosis, OSHC, or Pharmacy Location.")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle menu choice
    if not st.session_state.menu_choice:
        menu_choice = st.selectbox("Select a menu item:", options=["Diagnosis", "OSHC", "Pharmacy Location"])
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            st.rerun()  # Refresh the state to continue with the selected option
    
    # Process user input
    if st.session_state.menu_choice and st.session_state.showSelect:
        user_input = st.chat_input("What's up?")
        
        if user_input:
            # Display user input in chat and store the message
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            if user_input.lower() == "quit":
                # Reset chat and menu choice
                st.session_state.clear()
                st.rerun()  # Restart the chat flow
            # Generate response based on the menu choice
            elif st.session_state.menu_choice == 'OSHC':
                # response = get_response(user_input)
                st.write('OSHC')
            # with st.chat_message("assistant"):
            #     st.markdown(f'OK {st.session_state.menu_choice}')
            # response = f'OK {st.session_state.menu_choice}'
            elif st.session_state.menu_choice == 'Diagnosis':
                st.write('Diagnosis')
                # response = chat.test(user_input)
            # else:
            # Call get_response() function for other menu items
                # response = 'no'
            elif st.session_state.menu_choice == 'Pharmacy Location':
                st.write('Pharmacy Location')
                user_location = None
                response = "Please enter your location (address or postal code):"
                if user_input:
                    latitude, longitude = get_user_location(user_input)
                    if latitude is not None and longitude is not None:
                        user_location = (latitude, longitude)  # Tuple with lat/lon
                        nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages)
                        create_pharmacy_map(user_location, nearest_pharmacies)  # Display map with pharmacies
                    
                        response = "Here are the nearest pharmacies:"
                        for i, pharmacy in enumerate(nearest_pharmacies, 1):
                            response += f"\n{i}. {pharmacy['pharmacy_name']} - Distance: {pharmacy['distance']:.2f} km"
                    else:
                        response = "Sorry, I could not find your location. Please try again."
            else:
                    response = f"{st.session_state.menu_choice} chosen"
                    
                # Store and display response from the assistant
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

if __name__ == "__main__":
    main()
