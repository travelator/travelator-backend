import os
from langchain_community.chat_models import ChatPerplexity
from langchain.schema import HumanMessage
from dotenv import load_dotenv

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
        model="sonar-pro",  # Using a valid Perplexity model
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
    message = HumanMessage(content=query)
    
    # Get response from Perplexity
    response = perplexity_chain.invoke([message])
    
    # Return the content of the response
    return response.content

def main():
    # Setup the Perplexity chain
    perplexity_chain = setup_perplexity_chain()
    
    # Define activity and user input
    activity = "tour of parliament"
    user_input = "only return to me a link, with no other text, to a website where i can book the following activity: " + activity
    
    # Run the query and get response
    response = run_perplexity_query(perplexity_chain, user_input)
    
    # Print the response
    print(response)

if __name__ == "__main__":
    main()