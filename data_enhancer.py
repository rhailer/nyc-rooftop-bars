"""
Future enhancement script for pulling comprehensive rooftop bar data
This integrates with multiple APIs to get more complete venue information
"""

import requests
import json
import os
from typing import List, Dict
import time

class VenueDataEnhancer:
    def __init__(self):
        # API keys (add these to your .env file)
        self.yelp_api_key = os.getenv("YELP_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.foursquare_api_key = os.getenv("FOURSQUARE_API_KEY")
    
    def search_yelp_venues(self, location: str, term: str = "rooftop bar") -> List[Dict]:
        """Search Yelp for rooftop bars"""
        if not self.yelp_api_key:
            return []
        
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {self.yelp_api_key}"}
        params = {
            "term": term,
            "location": location,
            "categories": "bars,lounges",
            "limit": 50,
            "sort_by": "rating"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get("businesses", [])
        except Exception as e:
            print(f"Yelp API error: {e}")
        
        return []
    
    def search_google_places(self, location: str, query: str = "rooftop bar") -> List[Dict]:
        """Search Google Places for rooftop bars"""
        if not self.google_api_key:
            return []
        
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{query} in {location}",
            "key": self.google_api_key,
            "type": "bar"
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json().get("results", [])
        except Exception as e:
            print(f"Google Places API error: {e}")
        
        return []
    
    def enhance_venue_data(self, existing_data: List[Dict]) -> List[Dict]:
        """Enhance existing venue data with additional sources"""
        enhanced_data = existing_data.copy()
        
        # Add venues from different NYC areas
        nyc_areas = [
            "Manhattan, NY", "Brooklyn, NY", "Queens, NY", 
            "Bronx, NY", "Staten Island, NY"
        ]
        
        for area in nyc_areas:
            print(f"Searching {area}...")
            
            # Search Yelp
            yelp_venues = self.search_yelp_venues(area, "rooftop bar")
            for venue in yelp_venues:
                if "rooftop" in venue.get("name", "").lower() or \
                   any("rooftop" in cat.get("title", "").lower() for cat in venue.get("categories", [])):
                    
                    enhanced_venue = {
                        "name": venue.get("name"),
                        "address": ", ".join(venue.get("location", {}).get("display_address", [])),
                        "lat": venue.get("coordinates", {}).get("latitude"),
                        "lng": venue.get("coordinates", {}).get("longitude"),
                        "neighborhood": venue.get("location", {}).get("neighborhoods", [""])[0] if venue.get("location", {}).get("neighborhoods") else "",
                        "borough": area.split(",")[0],
                        "price_range": "$" * (venue.get("price", "$").count("$") or 2),
                        "vibe": f"Popular {venue.get('categories', [{}])[0].get('title', 'bar')} with great reviews",
                        "rating": venue.get("rating", 4.0),
                        "source": "yelp"
                    }
                    
                    # Check if venue already exists
                    if not any(existing.get("name", "").lower() == enhanced_venue["name"].lower() 
                             for existing in enhanced_data):
                        enhanced_data.append(enhanced_venue)
            
            # Rate limiting
            time.sleep(1)
        
        return enhanced_data

# Usage example:
if __name__ == "__main__":
    enhancer = VenueDataEnhancer()
    
    # Load existing data
    with open('data/rooftop_bars.json', 'r') as f:
        existing_data = json.load(f)
    
    # Enhance with additional sources
    enhanced_data = enhancer.enhance_venue_data(existing_data)
    
    # Save enhanced data
    with open('data/rooftop_bars_enhanced.json', 'w') as f:
        json.dump(enhanced_data, f, indent=2)
    
    print(f"Enhanced dataset: {len(existing_data)} -> {len(enhanced_data)} venues")