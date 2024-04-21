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

# Add the necessary imports and function definitions here
chat_history = []


# Initialize chat history if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []  # List of chat messages

# Define a function to get user latitude and longitude from an address
def get_user_location(address):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude  # Return lat/long
    else:
        return None, None

# Define a function to find the nearest pharmacies based on user location
def find_nearest_pharmacies(user_location, pharmacies, top_n=10):
    distances = []
    for _, pharmacy in pharmacies.iterrows():
        try:
            latitude = float(pharmacy["latitude"])
            longitude = float(pharmacy["longitude"])
            pharmacy_location = (latitude, longitude)
            distance = geodesic(user_location, pharmacy_location).kilometers
            distances.append((pharmacy, distance))
        except (ValueError, KeyError):
            continue  # Skip if latitude or longitude is invalid
    
    # Sort pharmacies by distance and return top N
    sorted_distances = sorted(distances, key=lambda x: x[1])
    return sorted_distances[:top_n]

# Define a function to create a Folium map with nearest pharmacies
def create_pharmacy_map(user_location, nearest_pharmacies):
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
            location=(pharmacy["latitude"], pharmacy["longitude"]),
            icon=folium.Icon(color="blue"),
        ).add_to(marker_cluster)

    return m

def main():
    # Set the title for your app
    st.title("Streamlit Chat")

    # Set a greeting message for the initial interaction
    greeting = "Hi, how can I help you? Choose from menu items: Diagnosis, OSHC, or Pharmacy Location."

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize menu choice and show/hide logic
    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = None

    if "showSelect" not in st.session_state:
        st.session_state.showSelect = False

    # Display the initial message from the assistant
    with st.chat_message("assistant"):
        st.markdown(greeting)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Display a select box for the user to choose a menu option
    if not st.session_state.menu_choice:
        menu_choice = st.selectbox("Select a menu item:", options=["Diagnosis", "OSHC", "Pharmacy Location"])
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            print(st.session_state)

    # Only display the select box if no menu choice has been made
    if not st.session_state.menu_choice:
        menu_choice = st.selectbox("Select a menu item:", options=["Diagnosis", "OSHC", "Pharmacy Location"], key="menu_selection")
    
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            st.write(f"You selected: {menu_choice}")  # Optional feedback to user

    # Further logic to handle menu choice
    if st.session_state.menu_choice == "Pharmacy Location":
        # Actions to perform when "Pharmacy Location" is selected
        st.write("You chose Pharmacy Location. Please provide your address for further assistance.")
    
        # Get user input for address
        address = st.text_input("Enter your address:")
    
        if st.button("Submit Address"):  # Button to submit the address
            # Store or process the address input
            st.write(f"You entered: {address}")
            # Store user message
            st.session_state.messages.append({
                "role": "user",
                "content": f"I'd like to know about pharmacies near this address: {address}",
            })
             # Get the user's location from the address
            user_latitude, user_longitude = get_user_location(address)

            if user_latitude and user_longitude:
                user_location = (user_latitude, user_longitude)

                # Find the nearest pharmacies
                nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages, top_n=10)

                if nearest_pharmacies:
                    # Create the map with the nearest pharmacies
                    map_object = create_pharmacy_map(user_location, nearest_pharmacies)

                    # Store assistant message and display the map
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Here's the map with the nearest pharmacies and their distances.",
                    })
                    folium_static(map_object)

                    # Display the top 10 nearest pharmacies in a table
                    nearest_pharmacies_df = pd.DataFrame(
                        [
                            (pharmacy["pharmacy_name"], f"{distance:.2f} km")
                            for pharmacy, distance in nearest_pharmacies
                        ],
                        columns=["Pharmacy Name", "Distance (km)"],
                    )
                    st.subheader("Top 10 Nearest Pharmacies:")
                    st.table(nearest_pharmacies_df)

                else:
                    # If no pharmacies are found near the user's location
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "No pharmacies found near your location.",
                    })
            else:
                # If the address couldn't be geocoded or isn't valid
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Address not found. Please check and try again.",
                })
    user_input = None
    if st.session_state.menu_choice is not None and st.session_state.showSelect is False:
      response = f'OK {st.session_state.menu_choice}'
      with st.chat_message("assistant"):   
        st.markdown(response)
      st.session_state.showSelect = True
      st.session_state.messages.append({"role": "assistant", "content": response})
    if st.session_state.menu_choice is not None:
      user_input = st.chat_input("What's up?")

    if user_input:
        # Display user input in chat message container
        with st.chat_message("user"):
            st.markdown(user_input)
        
        if user_input == 'quit':
          
          
          st.session_state.messages = []
          st.session_state.menu_choice = None
          st.session_state.showSelect = False
          response = 'Thanks'
          print(chat_history)
          st.experimental_rerun()
    
    # Additional logic for other menu choices
    elif st.session_state.menu_choice == "Diagnosis":
        st.write("Diagnosis option selected. Follow related steps.")

    elif st.session_state.menu_choice == "OSHC":
        st.write("OSHC option selected. Follow related steps.")
    
        if st.button("Send Address"):  # When user sends their address
            # Store user message
            st.session_state.messages.append({
                "role": "user",
                "content": f"I'd like to know about pharmacies near this address: {user_input}",
            })

# Call the main function to start the app
if __name__ == "__main__":
    main()
