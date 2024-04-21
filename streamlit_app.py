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

# Define function to get user latitude and longitude from an address
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude  # Return lat/long
    else:
        return None, None
    
# Define function to find the nearest pharmacies based on user location
def find_nearest_pharmacies(user_location, pharmacies):
    pharmacies["distance"] = pharmacies.apply(
        lambda row: geodesic(user_location, (row["latitude"], row["longitude"])).kilometers,
        axis=1  # Apply the function row-by-row to calculate distances
    )
    # Sort and get top 10 nearest pharmacies
    return pharmacies.sort_values("distance").head(10).to_dict(orient="records")

# Define a function to create a Folium map with nearest pharmacies
def create_pharmacy_map(user_location, nearest_pharmacies):
    m = folium.Map(location=user_location, zoom_start=15)
    marker_cluster = MarkerCluster().add_to(m)

    # Add a marker for user location
    folium.Marker(
        location=user_location,
        popup="Your Location",
        icon=folium.Icon(color="green")
    ).add_to(m)

    # Add markers for nearest pharmacies
    for pharmacy, distance in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']}<br>Distance: {distance:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            popup=popup_text,
            icon=folium.Icon(color="blue")
        ).add_to(marker_cluster)

    # Highlight the nearest pharmacy with a red marker
    nearest_pharmacy_location = (
        nearest_pharmacies[0]['latitude'], nearest_pharmacies[0]['longitude']
    )
    folium.Marker(
        location=nearest_pharmacy_location,
        popup="Nearest Pharmacy",
        icon=folium.Icon(color="red")
    ).add_to(m)

    folium_static(m)
    
    # Display top 10 nearest pharmacies
    nearest_pharmacies_df = pd.DataFrame(
        [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
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
        st.session_state.showSelect = False
    
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
            st.experimental_rerun()  # Refresh the state to continue with the selected option
    
    # If menu choice is set, process user input
    if st.session_state.menu_choice and not st.session_state.showSelect:
        with st.chat_message("assistant"):
            st.markdown(f'OK, you chose {st.session_state.menu_choice}. Please provide additional input.')

        st.session_state.showSelect = True
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f'OK, you chose {st.session_state.menu_choice}.'
        })
    
    if st.session_state.showSelect:
        user_input = st.chat_input("What's up?")
        
        if user_input:
            # Display user input in chat and store the message
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            if user_input.lower() == "quit":
                # Reset chat and menu choice
                st.session_state.clear()
                st.experimental_rerun()  # Restart the chat flow
            else:
                # Handle Pharmacy Location logic
                if st.session_state.menu_choice == 'Pharmacy Location':
                    user_location = get_user_location(user_input)
    
                    # Check if user location was successfully retrieved
                    if user_location[0] is not None and user_location[1] is not None:
                        nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages)
                        create_pharmacy_map(user_location, nearest_pharmacies)

                    # Generate a response listing nearest pharmacies
                    response = "Here are the nearest pharmacies:"
                    for i, (pharmacy, distance) in enumerate(nearest_pharmacies, 1):
                        response += f"\n{i}. {pharmacy['pharmacy_name']} - Distance: {distance:.2f} km"
                else:
                    # Error message if location cannot be found
                    response = "Sorry, I could not find your location. Please provide a valid address."
        else:
            response = f"{st.session_state.menu_choice} chosen" 

                # Store and display response from the assistant
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()