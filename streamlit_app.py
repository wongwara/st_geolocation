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
def find_nearest_pharmacies(user_location, yellow_pages):
    # Calculate distance between user location and all pharmacies
    yellow_pages["distance"] = yellow_pages.apply(
        lambda row: geodesic(user_location, (row["latitude"], row["longitude"])).kilometers,
        axis=1
    )
    # Sort pharmacies by distance and return the top 10 nearest pharmacies
    nearest_pharmacies = yellow_pages.sort_values("distance").head(10)
    return nearest_pharmacies.to_dict(orient="records")

# Define a function to create a Folium map with the nearest pharmacies
def create_pharmacy_map(user_location, nearest_pharmacies):
    # Create a Folium map centered on the user's location
    map_center = user_location
    m = folium.Map(location=map_center, zoom_start=15)

    # Create a MarkerCluster to group nearby markers
    marker_cluster = MarkerCluster().add_to(m)

    # Add a marker for the user's location
    folium.Marker(
        location=map_center,
        popup="Your Location",
        icon=folium.Icon(color="green")
    ).add_to(m)

    # Add markers for the nearest pharmacies with distance information
    for pharmacy, distance in nearest_pharmacies:
        popup_text = f"{pharmacy['pharmacy_name']}<br>Distance: {distance:.2f} km"
        folium.Marker(
            location=(pharmacy['latitude'], pharmacy['longitude']),
            popup=popup_text,
            icon=folium.Icon(color="blue")
        ).add_to(marker_cluster)

    # Highlight the nearest pharmacy with a red icon
    nearest_pharmacy_location = (nearest_pharmacies[0][0]['latitude'], nearest_pharmacies[0][0]['longitude'])
    folium.Marker(
        location=nearest_pharmacy_location,
        popup="Nearest Pharmacy",
        icon=folium.Icon(color="red")
    ).add_to(m)

    # Display the map and a table of the top 10 nearest pharmacies
    folium_static(m)

    nearest_pharmacies_df = pd.DataFrame(
        [(pharmacy['pharmacy_name'], f"{distance:.2f} km") for pharmacy, distance in nearest_pharmacies],
        columns=['Pharmacy Name', 'Distance (km)']
    )

    st.subheader("Top 10 Nearest Pharmacies:")
    st.table(nearest_pharmacies_df)

    return m

def main():
    global chat_history
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
    
    # if chat_history is None:
    #   chat_history = []
        
    # Display initial message
    with st.chat_message("assistant"):
        st.markdown(greeting)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle user input
    if not st.session_state.menu_choice:
        menu_choice = st.selectbox("Select a menu item:", options=["Diagnosis", "OSHC", "Pharmacy Location"])
        if st.button("Submit"):
            st.session_state.menu_choice = menu_choice
            print(st.session_state)
            # st.empty()
            
            # with st.chat_message("assistant"):
            #   st.markdown(f'OK {st.session_state.menu_choice}')
            # Perform any actions you want after submission
            
            st.experimental_rerun()

          
    # if st.session_state.menu_choice:
    #   with st.chat_message("assistant"):
    #     st.markdown(f'OK {st.session_state.menu_choice}')
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
          
        # Generate response based on the menu choice
        elif st.session_state.menu_choice == 'OSHC':
            st.write("OSHC")
        #   response = get_response(user_input)
          # with st.chat_message("assistant"):
          #     st.markdown(f'OK {st.session_state.menu_choice}')
          # response = f'OK {st.session_state.menu_choice}'
        elif st.session_state.menu_choice == 'Diagnosis':
            st.write("Diagnosis")
        #   response = chat.test(user_input)
        
        elif st.session_state.menu_choice == 'Pharmacy Location':
            user_location = get_user_location(user_input)
            if user_location[0] is not None:
                nearest_pharmacies = find_nearest_pharmacies(user_location, yellow_pages)
                pharmacy_map = create_pharmacy_map(user_location, nearest_pharmacies)
                folium_static(pharmacy_map)
                response = "Here are the nearest pharmacies to your location:"
                for i, (pharmacy, distance) in enumerate(nearest_pharmacies, 1):
                    response += f"\n{i}. {pharmacy['pharmacy_name']} - Distance: {distance:.2f} km"
            else:
                response = "Sorry, I could not find your location. Please try again!"
        
        else:
            # Call get_response() function for other menu items
            response = 'no'

        # Display bot response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Add user input and bot response to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": response})
        print(chat_history)
# Add the OSHC_chatbot() function here if needed

if __name__ == "__main__":
    
    main()

