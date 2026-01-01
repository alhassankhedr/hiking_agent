import requests
import json

def get_parks(api_key, state_code, country=None, latitude=None, longitude=None):
    """
    Fetches park data from the appropriate API based on country.
    For US: National Park Service API
    For Canada: OpenStreetMap Overpass API

    Args:
        api_key (str): The API key for the NPS API (required for US).
        state_code (str): The two-letter state/province code.
        country (str): The country code (e.g., 'US', 'CA').
        latitude (float): Latitude for location-based search (for Canada).
        longitude (float): Longitude for location-based search (for Canada).

    Returns:
        dict: A dictionary containing the API response with park data, 
              or None if an error occurs.
    """
    us_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC']
    
    # Check if it's Canada
    if country == 'CA':
        # Use OpenStreetMap for Canada
        return get_parks_canada(latitude, longitude, state_code)
    elif country == 'US' or (country is None and state_code in us_states):
        # Use NPS API for US
        return get_parks_us(api_key, state_code)
    else:
        # Default to OpenStreetMap for other countries or unknown
        return get_parks_canada(latitude, longitude, state_code)

def get_parks_us(api_key, state_code):
    """Fetches park data from the National Park Service (NPS) API for a given state."""
    url = f"https://developer.nps.gov/api/v1/parks?stateCode={state_code}&api_key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching parks data: {e}")
        return None

def get_parks_canada(latitude, longitude, province=None):
    """
    Fetches national parks in Canada using OpenStreetMap Overpass API.
    
    Args:
        latitude (float): Latitude for location-based search.
        longitude (float): Longitude for location-based search.
        province (str): Optional province name for filtering.
    
    Returns:
        dict: A dictionary in NPS-like format with park data, or None if an error occurs.
    """
    if not latitude or not longitude:
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
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            if overpass_url == overpass_servers[-1]:  # Last server, raise error
                print(f"Error fetching Canadian parks data from all servers: {e}")
                return None
            continue  # Try next server
    
    if not data:
        return None
    
    try:
        # Convert OpenStreetMap format to NPS-like format
        parks = []
        for element in data.get('elements', []):
            if 'tags' in element:
                tags = element['tags']
                park_name = tags.get('name', 'Unnamed Park')
                
                # Get coordinates
                if 'center' in element:
                    lat = element['center']['lat']
                    lon = element['center']['lon']
                elif 'lat' in element and 'lon' in element:
                    lat = element['lat']
                    lon = element['lon']
                else:
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
    For US: NPS API
    For Canada: OpenStreetMap Overpass API

    Args:
        api_key (str): The API key for the NPS API (required for US).
        park_code (str): The park code for the specific park.
        country (str): The country code (e.g., 'US', 'CA').
        park_lat (float): Park latitude (for Canada).
        park_lon (float): Park longitude (for Canada).
        park_name (str): Park name (for Canada).

    Returns:
        dict: A dictionary containing the API response with trail data, 
              or None if an error occurs.
    """
    if country == 'CA':
        return get_trails_canada(park_lat, park_lon, park_name)
    else:
        return get_trails_us(api_key, park_code)

def get_trails_us(api_key, park_code):
    """Fetches 'things to do' (including trails) from the NPS API for a specific park."""
    url = f"https://developer.nps.gov/api/v1/thingstodo?parkCode={park_code}&api_key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trails data: {e}")
        return None

def get_trails_canada(park_lat, park_lon, park_name):
    """
    Fetches hiking trails in a Canadian park using OpenStreetMap Overpass API.
    
    Args:
        park_lat (float): Park latitude.
        park_lon (float): Park longitude.
        park_name (str): Park name.
    
    Returns:
        dict: A dictionary in NPS-like format with trail data, or None if an error occurs.
    """
    if not park_lat or not park_lon:
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
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            if overpass_url == overpass_servers[-1]:  # Last server, raise error
                print(f"Error fetching Canadian trails data from all servers: {e}")
                return None
            continue  # Try next server
    
    if not data:
        return None
    
    try:
        
        trails = []
        seen_trails = set()  # Avoid duplicates
        
        for element in data.get('elements', []):
            if 'tags' in element:
                tags = element['tags']
                trail_name = tags.get('name', '')
                
                # Skip unnamed trails and duplicates
                if not trail_name or trail_name in seen_trails:
                    continue
                
                # Filter for hiking-related trails (more specific keywords)
                trail_lower = trail_name.lower()
                if any(keyword in trail_lower for keyword in ['trail', 'hiking', 'hike', 'loop', 'track']):
                    seen_trails.add(trail_name)
                    trails.append({
                        'title': trail_name,
                        'tags': ['hiking', 'trail'],
                        'description': tags.get('description', ''),
                    })
                    
                    # Limit results to prevent overwhelming responses
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
