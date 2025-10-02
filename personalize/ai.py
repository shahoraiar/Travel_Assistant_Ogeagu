# ai.py
import json
import os
import google.generativeai as genai
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Gemini API Key not configured: {e}")

# --- Logger ---
logger = logging.getLogger(__name__)


def generate_ai_plan(
    duration: int, 
    destination_name: str, 
    trip_type: str, 
    budget: str, 
    interests: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate an itinerary plan using Gemini AI's native JSON mode for reliability.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API key not configured or not available.")
        return {"itinerary_plan": []}

    # 1. MODEL UPGRADE: Use the faster, cheaper, and more modern Flash model.
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    # 2. CURRENT DATE: The current date is passed for temporal context.
    current_date_str = datetime.now().strftime('%B %d, %Y')
    
    # 3. PERSONALIZATION: Include user interests in the prompt.
    interests_prompt = ""
    if interests:
        interests_text = ", ".join(interests)
        interests_prompt = f"The traveler is particularly interested in: {interests_text}. Please tailor activities accordingly."

    prompt = f"""
    You are an expert travel planner. Today is {current_date_str}.   
    Create a detailed {duration}-day travel itinerary for {destination_name}.
    This is a {trip_type.lower()} trip with a {budget} daily budget.
    {interests_prompt}
    
    Your response must be a valid JSON object following these rules:
    - The root object must have a key "itinerary_plan" which is an array of day objects.
    - Each day object must have: "day" (number), "theme" (a creative theme for the day, e.g., "Historical Exploration"), and "activities" (an array).
    - Each activity object must have: "title" (a specific and engaging activity name) and "search_query" (a practical Google Maps search term).
    
    Make the search queries specific and useful. For example, for a museum in Paris, use "impressionist art museums near Louvre Paris" instead of just "museum".
    Ensure the plan is logical, balancing activities without being too rushed.
    """
    
    try:
        # 4. ROBUST JSON MODE: Force the model to output valid JSON.
        # This is more reliable than manual string cleaning.
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
        if not response.text:
            raise ValueError("Received an empty response from the AI model.")
        
        parsed_response = json.loads(response.text)
        
        # Validate the structure of the parsed response
        if not isinstance(parsed_response, dict) or "itinerary_plan" not in parsed_response:
            raise ValueError("AI response is missing the 'itinerary_plan' root key.")
            
        return parsed_response
        
    except json.JSONDecodeError as e:
        logger.error(f"Catastrophic failure to parse AI's JSON response: {e}")
        logger.error(f"Raw response from AI: {response.text if 'response' in locals() else 'No response available'}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during AI plan generation: {e}")
    
    return {"itinerary_plan": []}