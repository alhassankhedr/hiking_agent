def create_greeting(name: str) -> str:
    return f"Hello, {name}! Welcome to the world of AI Agents."

def run_agent():
    # Understand Intent
    user_name = input("What is your name: ")
    # Plan
    print("Agent: I should use the create_greeting function to greet the user.")
    # Use Tools
    greeting = create_greeting(user_name)
    # Reflect
    if greeting:
        print(f"Agent: {greeting}")
    else:
        print("Agent: I was unable to greet the user.")

if __name__ == "__main__":
    run_agent()
    