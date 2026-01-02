import geocoder

# Mapping of US state full names to their two-letter abbreviations
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
    """
    Determines the user's current location based on their IP address.

    Uses the geocoder library to perform IP-based geolocation. Converts
    full state names to abbreviations for US states. Validates coordinate
    ranges before returning.

    Returns:
        tuple: A tuple containing (latitude, longitude, state_abbrev, country).
            - latitude (float): Latitude coordinate (-90 to 90)
            - longitude (float): Longitude coordinate (-180 to 180)
            - state_abbrev (str or None): Two-letter state/province code
            - country (str or None): Country code (e.g., 'US', 'CA')
            Returns (None, None, None, None) if location cannot be determined
            or if coordinates are invalid.

    Raises:
        No exceptions are raised. All errors are caught and (None, None, None, None)
        is returned.

    Example:
        >>> lat, lon, state, country = get_current_location()
        >>> print(f"Location: {state}, {country} at ({lat}, {lon})")
    """
    try:
        g = geocoder.ip('me')
        if not g.ok or not g.latlng or len(g.latlng) < 2:
            print("Could not determine location from IP address.")
            return None, None, None, None
        
        latitude, longitude = g.latlng[0], g.latlng[1]
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return None, None, None, None
        
        state = getattr(g, 'state', None)
        state_abbrev = us_state_to_abbrev.get(state, state) if state else None
        country = getattr(g, 'country', None)
        
        return latitude, longitude, state_abbrev, country
    except Exception as e:
        print(f"Error during location lookup: {e}")
        return None, None, None, None

if __name__ == '__main__':
    # Example usage
    latitude, longitude, state, country = get_current_location()
    if latitude and longitude and state:
        print(f"Latitude: {latitude}, Longitude: {longitude}, State/Province: {state}, Country: {country}")
    else:
        print("Could not get your location.")
