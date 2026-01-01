import ollama
from weather import get_weather, get_todays_weather_summary
from parks import get_parks, get_trails
from location import get_current_location
from config import NPS_API_KEY

def query_model(system_prompt, user_prompt, messages=[]):
    """Generic function to query the Ollama model with memory."""
    messages.append({'role': 'user', 'content': user_prompt})
    
    # Add the system prompt to the start of the messages, if it's not already there
    if system_prompt and not any(d.get('role', None) == 'system' for d in messages):
        messages.insert(0, {'role': 'system', 'content': system_prompt})

    print("Asking model...")
    response = ollama.chat(model='gpt-oss:20b', messages=messages)
    
    response_content = response['message']['content'].strip()
    messages.append({'role': 'assistant', 'content': response_content})
    
    return response_content, messages

def is_final_answer(messages):
    """
    Uses the model to reflect on the conversation and determine if it has provided a final answer.
    """
    reflection_system_prompt = "You are a helpful assistant. Your task is to determine if the last response in this conversation is a complete and final answer to the user's request. The user may have asked for recommendations, and then asked follow-up questions. The last response should be a complete answer to the last question. Respond with only 'yes' or 'no'."
    
    # We don't want to add the reflection to the main chat history
    reflection_messages = messages[:]
    reflection_messages.append({'role': 'system', 'content': reflection_system_prompt})

    response = ollama.chat(model='gpt-oss:20b', messages=reflection_messages)
    decision = response['message']['content'].strip().lower()
    return "yes" in decision

def main():
    """
    Runs the main logic for the hiking agent.

    The agent performs the following steps:
    1. Gets the user's current location and today's weather forecast.
    2. Asks the model to decide if the weather is suitable for hiking.
    3. If the weather is good, it finds nearby national parks and trails.
    4. It then asks the model to provide opinionated hiking recommendations.
    """
    # --- Step 1: Get Location and Analyze Weather ---
    print("Detecting your location...")
    latitude, longitude, state, country = get_current_location()
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

    # --- Reflection 1: Decide if the weather is good enough for a hike ---
    weather_prompt = f"Based on this forecast, is it a good day for a hike? {weather_summary}"
    weather_system_prompt = "You are an assistant that determines if the weather is good for hiking. Respond with only 'yes' or 'no'."
    model_decision, _ = query_model(weather_system_prompt, weather_prompt) # We don't need history for this simple check
    print(f"Model decision: {model_decision}")

    if "no" in model_decision.lower():
        # Get detailed weather information and ask user how to proceed
        weather_info_prompt = f"""Analyze this weather forecast and provide a detailed explanation: {weather_summary}

Your task:
1. Explain specifically why this weather is not suitable for hiking (e.g., too cold, too hot, high precipitation, dangerous conditions)
2. Provide a friendly, helpful explanation
3. Then ask the user: "Would you like me to recommend indoor activities instead, or would you prefer to see hiking recommendations anyway despite the weather?"

Write a complete, detailed response. Do NOT just say "no" or "yes". Write full sentences explaining the weather concerns."""
        
        weather_info_system_prompt = "You are a helpful and friendly hiking assistant. You provide detailed, clear explanations. Always write complete sentences and be helpful. Never respond with just 'yes' or 'no'."
        weather_info, weather_messages = query_model(weather_info_system_prompt, weather_info_prompt)
        print(f"\n--- Weather Assessment ---")
        print(weather_info)
        
        # Ask user how to proceed
        user_choice = input("\nHow would you like to proceed? > ")
        
        if user_choice.lower() == 'exit':
            print("Goodbye! Stay safe!")
            return
        elif 'indoor' in user_choice.lower() or 'inside' in user_choice.lower() or 'activity' in user_choice.lower():
            # Provide indoor activity recommendations
            indoor_prompt = f"""The user is in {state}, {country if country else 'their location'}. The weather today is: {weather_summary}

The user wants recommendations for indoor activities. Provide 3-5 specific indoor activity recommendations that would be good for today given the weather conditions. Be specific and helpful. Include things like:
- Museums, galleries, or cultural centers
- Indoor sports or recreation facilities
- Shopping centers or markets
- Libraries or educational centers
- Indoor entertainment venues
- Any other relevant indoor activities

Provide detailed, helpful recommendations with brief explanations of why each might be enjoyable."""
            
            indoor_system_prompt = "You are a helpful activity recommendation assistant. Provide detailed, specific recommendations. Write complete sentences and be helpful. Never respond with just 'yes' or 'no'."
            indoor_response, _ = query_model(indoor_system_prompt, indoor_prompt)
            print(f"\n--- Indoor Activity Recommendations ---")
            print(indoor_response)
            return
        elif 'continue' in user_choice.lower() or 'hiking' in user_choice.lower() or 'trail' in user_choice.lower():
            print("\nContinuing with hiking recommendations despite the weather...")
        else:
            # Handle custom user request with proper context
            custom_prompt = f"""The user asked: "{user_choice}"

Context: The weather today is {weather_summary} and it's not ideal for hiking. The user is in {state}, {country if country else 'their location'}.

Help the user with their request. Provide detailed, helpful information. Write complete sentences."""
            response, _ = query_model("You are a helpful hiking and activity assistant. Always provide detailed, complete answers. Never respond with just 'yes' or 'no'.", custom_prompt)
            print(f"\nAgent: {response}")
            return
    
    # --- Step 2: Gather Park and Trail Data ---
    print("\nWeather looks good! Searching for nearby parks and trails...")
    parks_data = get_parks(NPS_API_KEY, state, country, latitude, longitude)

    if not parks_data or not parks_data.get("data"):
        location_name = state if country == 'US' else f"{state}, {country}" if country else state
        print(f"Could not find any National Parks near {location_name}.")
        return

    print("Analyzing parks and trails...")
    parks_and_trails = {}
    for park in parks_data["data"]:
        park_name = park['fullName']
        park_code = park.get('parkCode', '')
        park_lat = float(park.get('latitude', 0)) if park.get('latitude') else None
        park_lon = float(park.get('longitude', 0)) if park.get('longitude') else None
        
        trails_data = get_trails(NPS_API_KEY, park_code, country, park_lat, park_lon, park_name)
        if not trails_data:
            continue
        
        if trails_data.get("data"):
            # Simplified trail filtering
            trails_list = [
                trail['title'] for trail in trails_data["data"]
                if "hiking" in trail.get("tags", []) or "trail" in trail.get("title", "").lower()
            ]
            parks_and_trails[park_name] = trails_list

    # --- Step 3: Get Opinionated Recommendations from Model ---
    print("Asking the model for hiking recommendations...")
    recommendations_system_prompt = "You are an expert hiking guide. Your task is to analyze the following list of parks and trails and recommend the top 2-3 options for a hike today. Provide a brief, opinionated reason for each recommendation, explaining why it's a good choice (e.g., 'Best for views,' 'Great for a challenge,' 'Perfect for a relaxing walk'). Always write complete sentences with detailed recommendations. Never respond with just 'yes' or 'no'."
    
    prompt_data = ""
    for park_name, trails in parks_and_trails.items():
        prompt_data += f"\nPark: {park_name}\n"
        if trails:
            for trail in trails:
                prompt_data += f"  - Trail: {trail}\n"
        else:
            prompt_data += "  - No specific trails listed.\n"
    
    recommendations_prompt = f"""Here are the available parks and trails near the user:

{prompt_data}

Analyze these options and provide your top 2-3 hiking recommendations. For each recommendation, include:
1. The park and trail name
2. Why it's a good choice
3. What makes it special

Write a complete, detailed response with full recommendations. Do NOT respond with just 'yes' or 'no'."""
            
    recommendations, message_history = query_model(recommendations_system_prompt, recommendations_prompt)
    print("\n--- Hiking Recommendations ---")
    print(recommendations)

    # --- Step 4: Handle Follow-up Questions ---
    followup_system_prompt = "You are a helpful hiking and activity assistant. You have access to information about parks, trails, weather, and activities. Always provide detailed, complete answers to user questions. Be helpful, friendly, and informative. Never respond with just 'yes' or 'no' - always provide full explanations and helpful information."
    
    while True:
        follow_up_prompt = input("\nDo you have any follow-up questions? (type 'exit' to quit) > ")
        if follow_up_prompt.lower() == 'exit':
            break

        # Use proper system prompt for follow-ups to ensure detailed responses
        response, message_history = query_model(followup_system_prompt, follow_up_prompt, message_history)
        print(f"\nAgent: {response}")

        # --- Reflection 2: Decide if the answer is final ---
        if is_final_answer(message_history):
            print("Agent reflects: I believe I have answered the question.")
        else:
            print("Agent reflects: I may need to ask for more information or clarify.")

if __name__ == '__main__':
    main()
