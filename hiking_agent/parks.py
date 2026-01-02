import requests
import json

def get_parks(api_key, state_code, country=None, latitude=None, longitude=None):
    """
    Fetches park data from the appropriate API based on country.

    Routes to the correct API based on country code:
    - US: Uses National Park Service (NPS) API
    - Canada and other countries: Uses OpenStreetMap Overpass API

    Args:
        api_key (str): The API key for the NPS API. Required for US searches.
        state_code (str): The two-letter state/province code (e.g., 'CA', 'NY').
        country (str, optional): The country code (e.g., 'US', 'CA').
            If None and state_code is a US state, defaults to US.
        latitude (float, optional): Latitude for location-based search.
            Required for non-US searches (Canada and others).
        longitude (float, optional): Longitude for location-based search.
            Required for non-US searches (Canada and others).

    Returns:
        dict or None: A dictionary containing the API response with park data.
            The response includes a 'data' key with a list of park dictionaries.
            Each park dict contains 'fullName', 'parkCode', 'latitude', 'longitude'.
            Returns None if required parameters are missing or if an error occurs.

    Example:
        >>> parks = get_parks(api_key, "CA", country="US")
        >>> print(parks['data'][0]['fullName'])
        "Yosemite National Park"
    """
    us_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC']
    
    if country == 'CA' or (country != 'US' and state_code not in us_states):
        if latitude is None or longitude is None:
            return None
        return get_parks_canada(latitude, longitude, state_code)
    else:
        if not api_key:
            return None
        return get_parks_us(api_key, state_code)

def get_parks_us(api_key, state_code):
    """
    Fetches park data from the National Park Service (NPS) API for a given state.

    Args:
        api_key (str): The NPS API key obtained from developer.nps.gov.
        state_code (str): Two-letter US state code (e.g., 'CA', 'NY', 'TX').

    Returns:
        dict or None: A dictionary containing the NPS API response with park data.
            The response includes a 'data' key with a list of park dictionaries.
            Returns None if the API request fails or if parameters are invalid.

    Raises:
        No exceptions are raised. All errors are caught and None is returned.
    """
    url = f"https://developer.nps.gov/api/v1/parks?stateCode={state_code}&api_key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching parks data: {e}")
        return None

def get_parks_canada(latitude, longitude, province=None):
    """
    Fetches national parks in Canada using OpenStreetMap Overpass API.

    Searches for national parks within 150km of the specified coordinates.
    Tries multiple Overpass API servers for reliability. Converts OpenStreetMap
    data format to match the NPS API format for consistency.

    Args:
        latitude (float): Latitude coordinate for location-based search (-90 to 90).
        longitude (float): Longitude coordinate for location-based search (-180 to 180).
        province (str, optional): Province name for filtering. Currently not used
            in the query but kept for future enhancement.

    Returns:
        dict or None: A dictionary in NPS-like format with park data.
            The response includes a 'data' key with a list of park dictionaries.
            Each park dict contains 'fullName', 'parkCode', 'latitude', 'longitude',
            and 'description'. Returns None if coordinates are invalid or if
            the API request fails.

    Raises:
        No exceptions are raised. All errors are caught and None is returned.
    """
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return None
    except (ValueError, TypeError):
        return None
    
    # Search radius: 150km around the location (reduced from 200km for better performance)
    radius = 150000  # in meters
    
    # Try faster server first, fallback to default
    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    
    # Optimized query - only relations (faster than ways), shorter timeout
    query = f"""
    [out:json][timeout:10];
    (
      relation["boundary"="national_park"]["name"](around:{radius},{latitude},{longitude});
    );
    out center tags;
    """
    
    data = None
    for overpass_url in overpass_servers:
        try:
            response = requests.post(overpass_url, data={'data': query}, timeout=15)
            response.raise_for_status()
            data = response.json()
            break
        except requests.exceptions.RequestException:
            if overpass_url == overpass_servers[-1]:
                print("Error fetching Canadian parks data.")
                return None
            continue
    
    if not data or not isinstance(data, dict):
        return None
    
    try:
        parks = []
        for element in data.get('elements', []):
            if not isinstance(element, dict) or 'tags' not in element:
                continue
            
            tags = element.get('tags', {})
            park_name = tags.get('name')
            if not park_name:
                continue
            
            # Get coordinates
            if 'center' in element:
                lat = element['center'].get('lat')
                lon = element['center'].get('lon')
            else:
                lat = element.get('lat')
                lon = element.get('lon')
            
            if lat is None or lon is None:
                continue
            
            parks.append({
                'fullName': park_name,
                'parkCode': park_name.replace(' ', '').replace("'", "")[:10].upper(),
                'latitude': str(lat),
                'longitude': str(lon),
                'description': tags.get('description', tags.get('wikipedia', '')),
            })
        
        return {'data': parks} if parks else None
    except Exception as e:
        print(f"Error processing Canadian parks data: {e}")
        return None

def get_trails(api_key, park_code, country=None, park_lat=None, park_lon=None, park_name=None):
    """
    Fetches trails data from the appropriate API based on country.

    Routes to the correct API based on country code:
    - US: Uses NPS API "things to do" endpoint
    - Canada: Uses OpenStreetMap Overpass API

    Args:
        api_key (str): The API key for the NPS API. Required for US searches.
        park_code (str): The park code for the specific park (e.g., 'YOSE' for Yosemite).
        country (str, optional): The country code (e.g., 'US', 'CA').
        park_lat (float, optional): Park latitude. Required for Canadian searches.
        park_lon (float, optional): Park longitude. Required for Canadian searches.
        park_name (str, optional): Park name. Used for Canadian searches.

    Returns:
        dict or None: A dictionary containing the API response with trail data.
            The response includes a 'data' key with a list of trail dictionaries.
            Each trail dict contains 'title', 'tags', and 'description'.
            Returns None if required parameters are missing or if an error occurs.

    Example:
        >>> trails = get_trails(api_key, "YOSE", country="US")
        >>> print(trails['data'][0]['title'])
        "Half Dome Trail"
    """
    if country == 'CA':
        return get_trails_canada(park_lat, park_lon, park_name)
    else:
        return get_trails_us(api_key, park_code)

def get_trails_us(api_key, park_code):
    """
    Fetches 'things to do' (including trails) from the NPS API for a specific park.

    The NPS API "things to do" endpoint returns various activities including
    hiking trails, scenic drives, and other recreational activities.

    Args:
        api_key (str): The NPS API key obtained from developer.nps.gov.
        park_code (str): The park code for the specific park (e.g., 'YOSE', 'GRCA').

    Returns:
        dict or None: A dictionary containing the NPS API response with activity data.
            The response includes a 'data' key with a list of activity dictionaries.
            Each activity dict contains 'title', 'tags', 'description', etc.
            Returns None if the API request fails or if parameters are invalid.

    Raises:
        No exceptions are raised. All errors are caught and None is returned.
    """
    url = f"https://developer.nps.gov/api/v1/thingstodo?parkCode={park_code}&api_key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trails data: {e}")
        return None

def get_trails_canada(park_lat, park_lon, park_name):
    """
    Fetches hiking trails in a Canadian park using OpenStreetMap Overpass API.

    Searches for hiking routes and paths within 10km of the park coordinates.
    Filters results to include only trails with names containing keywords like
    'trail', 'hiking', 'hike', 'loop', or 'track'. Limits results to 20 trails
    to prevent overwhelming responses. Tries multiple Overpass API servers
    for reliability.

    Args:
        park_lat (float): Park latitude coordinate (-90 to 90).
        park_lon (float): Park longitude coordinate (-180 to 180).
        park_name (str): Park name. Currently used for context but not in the query.

    Returns:
        dict or None: A dictionary in NPS-like format with trail data.
            The response includes a 'data' key with a list of trail dictionaries.
            Each trail dict contains 'title', 'tags' (always ['hiking', 'trail']),
            and 'description'. Returns None if coordinates are invalid or if
            the API request fails.

    Raises:
        No exceptions are raised. All errors are caught and None is returned.
    """
    try:
        park_lat = float(park_lat)
        park_lon = float(park_lon)
        if not (-90 <= park_lat <= 90) or not (-180 <= park_lon <= 180):
            return None
    except (ValueError, TypeError):
        return None
    
    # Search radius: 10km around the park (reduced from 50km to avoid timeouts)
    radius = 10000  # in meters
    
    # Try faster server first, fallback to default
    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    
    # Optimized query - more specific, smaller radius, shorter timeout
    # Prioritize hiking routes over generic paths
    query = f"""
    [out:json][timeout:8];
    (
      relation["route"="hiking"]["name"](around:{radius},{park_lat},{park_lon});
      way["highway"="path"]["name"](around:{radius},{park_lat},{park_lon});
    );
    out tags;
    """
    
    data = None
    for overpass_url in overpass_servers:
        try:
            response = requests.post(overpass_url, data={'data': query}, timeout=12)
            response.raise_for_status()
            data = response.json()
            break
        except requests.exceptions.RequestException:
            if overpass_url == overpass_servers[-1]:
                print("Error fetching Canadian trails data.")
                return None
            continue
    
    if not data or not isinstance(data, dict):
        return None
    
    try:
        trails = []
        seen_trails = set()
        for element in data.get('elements', []):
            if not isinstance(element, dict) or 'tags' not in element:
                continue
            
            tags = element.get('tags', {})
            trail_name = tags.get('name', '')
            
            if not trail_name or trail_name in seen_trails:
                continue
            
            trail_lower = trail_name.lower()
            if any(keyword in trail_lower for keyword in ['trail', 'hiking', 'hike', 'loop', 'track']):
                seen_trails.add(trail_name)
                trails.append({
                    'title': trail_name,
                    'tags': ['hiking', 'trail'],
                    'description': tags.get('description', ''),
                })
                
                if len(trails) >= 20:
                    break
        
        return {'data': trails} if trails else None
    except Exception as e:
        print(f"Error processing Canadian trails data: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    from config import NPS_API_KEY
    
    # Example for US
    print("=== US Example (California) ===")
    state_code = "CA"  # Example state code for California
    parks_data = get_parks(NPS_API_KEY, state_code, country='US')
    
    if parks_data and "data" in parks_data and parks_data["data"]:
        # Get trails for the first park in the list
        park = parks_data["data"][0]
        park_code = park.get("parkCode", "")
        park_lat = float(park.get('latitude', 0)) if park.get('latitude') else None
        park_lon = float(park.get('longitude', 0)) if park.get('longitude') else None
        trails_data = get_trails(NPS_API_KEY, park_code, country='US', park_lat=park_lat, park_lon=park_lon, park_name=park['fullName'])
        
        if trails_data and "data" in trails_data:
            print(f"Trails in {park['fullName']}:")
            for trail in trails_data["data"]:
                print(trail["title"])
        else:
            print("Could not fetch trails data.")
    else:
        print("Could not fetch parks data. Please check your API key and state code.")
    
    # Example for Canada
    print("\n=== Canada Example (Toronto area) ===")
    # Toronto coordinates
    toronto_lat = 43.6532
    toronto_lon = -79.3832
    province = "Ontario"
    
    parks_data_ca = get_parks(NPS_API_KEY, province, country='CA', latitude=toronto_lat, longitude=toronto_lon)
    
    if parks_data_ca and "data" in parks_data_ca and parks_data_ca["data"]:
        print(f"Found {len(parks_data_ca['data'])} parks near Toronto:")
        for park in parks_data_ca["data"][:3]:  # Show first 3 parks
            print(f"  - {park['fullName']}")
            park_lat = float(park.get('latitude', 0)) if park.get('latitude') else None
            park_lon = float(park.get('longitude', 0)) if park.get('longitude') else None
            
            # Get trails for this park
            trails_data = get_trails(NPS_API_KEY, park.get('parkCode', ''), country='CA', 
                                   park_lat=park_lat, park_lon=park_lon, park_name=park['fullName'])
            if trails_data and "data" in trails_data:
                print(f"    Trails: {len(trails_data['data'])} found")
                for trail in trails_data["data"][:2]:  # Show first 2 trails
                    print(f"      - {trail['title']}")
            else:
                print("    No trails found")
    else:
        print("Could not fetch Canadian parks data.")
