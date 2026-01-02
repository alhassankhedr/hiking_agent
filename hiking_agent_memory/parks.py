import requests

def get_parks(api_key, state_code):
    url = f"https://developer.nps.gov/api/v1/parks?stateCode={state_code}&api_key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching parks data: {e}")
        return {}
    except ValueError:
        print("Failed to decode parks data from response.")
        return {}

def get_trails(api_key, park_code):
    url = f"https://developer.nps.gov/api/v1/thingstodo?parkCode={park_code}&api_key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching trails data: {e}")
        return {}
    except ValueError:
        print("Failed to decode trails data from response.")
        return {}

if __name__ == '__main__':
    # Example usage
    from config import NPS_API_KEY
    state_code = "CA"  # Example state code for California
    parks_data = get_parks(NPS_API_KEY, state_code)
    
    if "data" in parks_data and parks_data["data"]:
        # Get trails for the first park in the list
        park_code = parks_data["data"][0]["parkCode"]
        trails_data = get_trails(NPS_API_KEY, park_code)
        
        if "data" in trails_data:
            print(f"Trails in {parks_data['data'][0]['fullName']}:")
            for trail in trails_data["data"]:
                print(trail["title"])
        else:
            print("Could not fetch trails data.")
    else:
        print("Could not fetch parks data. Please check your API key and state code.")
