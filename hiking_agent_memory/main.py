import ollama
from weather import get_weather, get_todays_weather_summary
from parks import get_parks, get_trails
from location import get_current_location
from config import NPS_API_KEY

def query_model(system_prompt, user_prompt, messages=None):
    """Generic function to query the Ollama model with memory."""
    if messages is None:
        messages = []
    
    messages.append({'role': 'user', 'content': user_prompt})
    
    if system_prompt and not any(d.get('role', None) == 'system' for d in messages):
        messages.insert(0, {'role': 'system', 'content': system_prompt})

    try:
        print("Asking model...")
        response = ollama.chat(model='gpt-oss:20b', messages=messages)
        
        response_content = response['message']['content'].strip()
        messages.append({'role': 'assistant', 'content': response_content})
        
        return response_content, messages
    except Exception as e:
        print(f"An error occurred while querying the model: {e}")
        # Remove the user message that caused the error
        messages.pop()
        return "", messages

def main():
    if NPS_API_KEY == "YOUR_API_KEY_HERE":
        print("Please set your NPS_API_KEY in config.py before running the script.")
        return

    # --- Step 1: Get Location and Analyze Weather ---
    print("Detecting your location...")
    latitude, longitude, state = get_current_location()
    if not latitude:
        print("Could not detect your location. Please restart and try again.")
        return

    print("Checking the weather near you...")
    weather_data = get_weather(latitude, longitude)
    if not weather_data:
        print("Could not retrieve weather data. Please try again later.")
        return
    weather_summary = get_todays_weather_summary(weather_data)
    print(f"Weather Summary: {weather_summary}")

    if "Could not get" in weather_summary:
        print("Could not get a valid weather summary. Exiting.")
        return

    weather_prompt = f"Based on this forecast, is it a good day for a hike? {weather_summary}"
    weather_system_prompt = "You are an assistant that determines if the weather is good for hiking. Respond with only 'yes' or 'no'."
    model_decision, _ = query_model(weather_system_prompt, weather_prompt) # Don't need history for this
    model_decision = model_decision.lower()
    
    if not model_decision:
        print("The model failed to provide a weather decision. Please try again later.")
        return
    
    print(f"Model decision: {model_decision}")

    # --- Step 2: Gather Park and Trail Data (Now always runs)---
    print("\nSearching for nearby parks and trails...")
    parks_data = get_parks(NPS_API_KEY, state)

    if not parks_data or not parks_data.get("data"):
        print(f"Could not find any National Parks in {state}.")
        return

    parks_and_trails = {}
    for park in parks_data["data"]:
        park_name = park['fullName']
        trails_data = get_trails(NPS_API_KEY, park["parkCode"])
        
        if trails_data and trails_data.get("data"):
            # Simplified trail filtering
            trails_list = [
                trail['title'] for trail in trails_data["data"]
                if "hiking" in trail.get("tags", []) or "trail" in trail.get("title", "").lower()
            ]
            parks_and_trails[park_name] = trails_list

    if not parks_and_trails:
        print("No parks with hiking trails found in your area.")
        return

    # --- Step 3: Get Opinionated Recommendations from Model ---
    # The Python code will handle the weather logic, not the LLM.
    if "no" in model_decision:
        print("\nWeather is not suitable for hiking today. Here are some parks you could consider for a future trip:")
    else:
        print("\nWeather looks good! Asking the model for hiking recommendations...")

    recommendations_system_prompt = "You are an expert hiking guide. Your task is to analyze the following list of parks and trails and recommend the top 2-3 options for a hike. Provide a brief, opinionated reason for each recommendation, explaining why it's a good choice (e.g., 'Best for views,' 'Great for a challenge,' 'Perfect for a relaxing walk')."
    
    prompt_data = ""
    for park_name, trails in parks_and_trails.items():
        prompt_data += f"\nPark: {park_name}\n"
        if trails:
            for trail in trails:
                prompt_data += f"  - Trail: {trail}\n"
        else:
            prompt_data += "  - No specific trails listed.\n"
            
    recommendations, message_history = query_model(recommendations_system_prompt, prompt_data)
    print("\n--- Hiking Recommendations ---")
    print(recommendations)

    # --- Step 4: Handle Follow-up Questions ---
    while True:
        follow_up_prompt = input("\nDo you have any follow-up questions? (type 'exit' to quit) > ")
        if follow_up_prompt.lower() == 'exit':
            break

        # Normal follow-up question
        response, message_history = query_model("", follow_up_prompt, message_history)
        print(f"\nAgent: {response}")

if __name__ == '__main__':
    main()
