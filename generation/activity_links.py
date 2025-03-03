import os
from langchain_community.chat_models import ChatPerplexity
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
import ast


# Load environment variables from .env file (if you have one)
load_dotenv()

def setup_perplexity_chain():
    """
    Set up and return a Perplexity chat model using the API key.
    
    Returns:
        ChatPerplexity: A configured Perplexity chat model instance
    """
    # Get API key from environment variables, or set it directly here
    # (Best practice is to use environment variables for security)
    api_key = os.getenv("PERPLEXITY_API_KEY")
    
    # If the API key is not in environment variables, you can set it directly
    if not api_key:
        # Replace with your actual Perplexity API key
        api_key = "YOUR_PERPLEXITY_API_KEY"
    
    # Initialize the Perplexity chat model
    # You can adjust model parameters as needed
    chat_model = ChatPerplexity(
        api_key=api_key,
        model="sonar",  # Using a valid Perplexity model
        temperature=0.7
    )
    
    return chat_model

def run_perplexity_query(perplexity_chain, query):
    """
    Send a query to the Perplexity API and return the response.
    
    Args:
        perplexity_chain (ChatPerplexity): The Perplexity chat model
        query (str): The user query string
    
    Returns:
        str: The response from Perplexity
    """
    # Create a message with the query
    system_message = SystemMessage(content="If there is no link to return, just reply with None. Do not add any comments as I will turn this output into a dictionary.")
    human_message = HumanMessage(content=query)
    
    # Get response from Perplexity
    response = perplexity_chain.invoke([system_message, human_message])
    
    # Return the content of the response
    return response.content

def get_activity_links(titles_set):
    """
    Get booking links for activities using Perplexity API.
    Returns results as a dictionary where each activity is a key and its link is the value.
    
    Args:
        titles_set (set): A set containing activity descriptions
        
    Returns:
        dict: Dictionary with activities as keys and their booking links as values
    """
    perplexity_chain = setup_perplexity_chain()
    
    user_input = "replace each value in this dictionary with a ideally a booking link, otherwise a website link, related to that activity and return only the dictionary with no other text as a string: " + str(titles_set)
    perplexity_output = run_perplexity_query(perplexity_chain, user_input)
    cleaned_string = perplexity_output.strip('```python\n').strip('```')
    
    try:
        # Attempt to convert the cleaned string to a dictionary
        result_dict = ast.literal_eval(cleaned_string)
        
        # Check if the result is indeed a dictionary
        if isinstance(result_dict, dict):
            return result_dict
        else:
            return None
    except (ValueError, SyntaxError):
        # If there's an error during evaluation, return None
        return None

if __name__ == "__main__":
    titles = {"1": "tour of buckingham palace", "2": "tour of tower of london", "3": "tour of parliament", "4": "tour of the white house", "5": "tour of the british museum"}
    response = get_activity_links(titles)
    print(response)