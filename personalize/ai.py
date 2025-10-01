# ai.py
import json
import os
import google.generativeai as genai # type: ignore
import json
import logging
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Gemini API Key not configured: {e}")

# --- Logger ---
logger = logging.getLogger(__name__)


def generate_ai_plan(duration: int, destination_name: str, trip_type: str, budget: str) -> Dict[str, Any]:
    """
    Generate itinerary plan with searchable queries using Gemini AI
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API key not available")
        return {"itinerary_plan": []}

    model = genai.GenerativeModel("gemini-pro")
    
    # Enhanced prompt with better structure
    prompt = f"""
    Create a detailed {duration}-day travel itinerary for {destination_name} for a {trip_type.lower()} trip with a {budget} budget.
    
    CRITICAL REQUIREMENTS:
    1. Return ONLY valid JSON - no other text, no markdown, no code blocks
    2. JSON structure must have root key "itinerary_plan" containing an array of day objects
    3. Each day object must have: "day" (number), "theme" (string), "activities" (array)
    4. Each activity must have: "title" (specific activity), "search_query" (Google Maps search term)
    
    IMPORTANT: Make search queries specific and location-aware. Examples:
    - Instead of "museum", use "art museums in {destination_name}"
    - Instead of "restaurant", use "highly rated local cuisine restaurants in {destination_name} city center"
    - Include location context in search queries
    
    Balance activities throughout each day and consider realistic travel times.
    
    Response must be valid JSON only:
    """
    
    try:
        response = model.generate_content(prompt)
        
        if not response.text:
            raise ValueError("Empty response from AI model")
        
        # Clean response text
        cleaned_response = response.text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        parsed_response = json.loads(cleaned_response)
        
        # Validate response structure
        if not isinstance(parsed_response, dict) or "itinerary_plan" not in parsed_response:
            raise ValueError("Invalid response structure from AI")
            
        return parsed_response
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
    except Exception as e:
        logger.error(f"Error generating AI plan: {e}")
    
    return {"itinerary_plan": []}