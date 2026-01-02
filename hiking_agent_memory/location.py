import geocoder

us_state_to_abbrev = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
}

def get_current_location():
    try:
        g = geocoder.ip('me')
        if g.ok:
            state_abbrev = us_state_to_abbrev.get(g.state, g.state)
            return g.latlng[0], g.latlng[1], state_abbrev
        else:
            print("Failed to get location.")
            return None, None, None
    except Exception as e:
        print(f"An error occurred while getting location: {e}")
        return None, None, None

if __name__ == '__main__':
    # Example usage
    latitude, longitude, state = get_current_location()
    if latitude and longitude and state:
        print(f"Latitude: {latitude}, Longitude: {longitude}, State: {state}")
    else:
        print("Could not get your location.")
