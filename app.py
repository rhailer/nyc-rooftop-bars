import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import openai
from dotenv import load_dotenv
import os
import urllib.parse
from typing import Dict, List, Tuple, Optional

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Nature in NYC | Rooftop Bar Finder",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

# Streamlit-Safe Professional CSS
st.markdown("""
<style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Dark Theme */
    .stApp {
        background-color: #0f0f0f;
        color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* Main Container */
    .main .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
    
    /* Professional Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2d7ff9, #1e40af) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
        height: 48px !important;
        box-shadow: 0 4px 12px rgba(45, 127, 249, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        filter: brightness(1.1) !important;
        box-shadow: 0 8px 20px rgba(45, 127, 249, 0.4) !important;
    }
    
    /* Select Boxes */
    .stSelectbox > div > div {
        background-color: #202020 !important;
        border: 1px solid #2d2d2d !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 500 !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #2d7ff9 !important;
        box-shadow: 0 0 0 3px rgba(45, 127, 249, 0.1) !important;
    }
    
    /* Metrics */
    div[data-testid="metric-container"] {
        background: #202020;
        border: 1px solid #2d2d2d;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    div[data-testid="metric-container"] > div {
        color: #ffffff;
    }
    
    /* Expandable sections */
    .streamlit-expanderHeader {
        background-color: #202020 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    
    .streamlit-expanderContent {
        background-color: #1a1a1a !important;
        border-radius: 0 0 8px 8px !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: rgba(0, 200, 150, 0.1) !important;
        border: 1px solid #00c896 !important;
        color: #00c896 !important;
        border-radius: 8px !important;
    }
    
    .stError {
        background-color: rgba(255, 71, 87, 0.1) !important;
        border: 1px solid #ff4757 !important;
        color: #ff4757 !important;
        border-radius: 8px !important;
    }
    
    .stWarning {
        background-color: rgba(255, 176, 0, 0.1) !important;
        border: 1px solid #ffb000 !important;
        color: #ffb000 !important;
        border-radius: 8px !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Custom spacing */
    .custom-header {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, rgba(45, 127, 249, 0.1), rgba(30, 64, 175, 0.1));
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid #2d2d2d;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #2d7ff9, #1e40af);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #b4b4b4;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    .tagline {
        color: #6b7280;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Card styling for containers */
    .search-card {
        background: #202020;
        border: 1px solid #2d2d2d;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem !important;
        }
        .subtitle {
            font-size: 1rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def get_openai_key():
    """Get OpenAI API key from environment or Streamlit secrets"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
        except:
            pass
    return api_key

class RooftopBarFinder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="elevate_nyc_finder")
        
        # Initialize OpenAI if key available
        openai_key = get_openai_key()
        if openai_key:
            openai.api_key = openai_key
        
        self.load_bars_data()
        
        self.nyc_neighborhoods = {
            "Manhattan": [
                "SoHo", "Greenwich Village", "East Village", "West Village", 
                "Tribeca", "Financial District", "Lower East Side", "Nolita",
                "Little Italy", "Chinatown", "Chelsea", "Meatpacking District",
                "Flatiron", "Union Square", "Gramercy", "NoMad", "Murray Hill",
                "Midtown East", "Midtown West", "Times Square", "Hell's Kitchen",
                "Upper East Side", "Upper West Side", "Morningside Heights",
                "Harlem", "East Harlem", "Washington Heights", "Inwood"
            ],
            "Brooklyn": [
                "DUMBO", "Brooklyn Heights", "Cobble Hill", "Carroll Gardens",
                "Williamsburg", "Greenpoint", "Bushwick", "Park Slope", 
                "Prospect Heights", "Crown Heights", "Red Hook", "Sunset Park"
            ],
            "Queens": [
                "Long Island City", "Astoria", "Sunnyside", "Jackson Heights",
                "Elmhurst", "Flushing", "Forest Hills"
            ],
            "Bronx": [
                "Mott Haven", "Port Morris", "Fordham", "Riverdale"
            ],
            "Staten Island": [
                "St. George", "Stapleton", "Port Richmond"
            ]
        }
    
    def load_bars_data(self):
        """Load rooftop bars data"""
        try:
            with open('data/rooftop_bars.json', 'r') as f:
                self.bars_data = json.load(f)
        except FileNotFoundError:
            st.error("🚨 Bars data file not found. Please check data/rooftop_bars.json")
            self.bars_data = []
    
    def generate_bar_links(self, bar: Dict) -> Dict:
        """Generate search links"""
        name = urllib.parse.quote_plus(f"{bar.get('name', '')} NYC")
        address = urllib.parse.quote_plus(bar.get('address', ''))
        
        return {
            'yelp': f"https://www.yelp.com/search?find_desc={name}&find_loc=New+York%2C+NY",
            'maps': f"https://www.google.com/maps/search/?api=1&query={address}",
            'opentable': f"https://www.opentable.com/s?query={name}"
        }
    
    def get_neighborhood_center(self, neighborhood: str, borough: str) -> Tuple[Optional[float], Optional[float]]:
        """Get coordinates for neighborhood"""
        try:
            query = f"{neighborhood}, {borough}, New York, NY"
            location = self.geolocator.geocode(query)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            st.error(f"Error finding location: {e}")
            return None, None
    
    def calculate_distance(self, user_coords: Tuple[float, float], bar_coords: Tuple[float, float]) -> float:
        """Calculate distance"""
        return geodesic(user_coords, bar_coords).miles
    
    def get_bars_nearby(self, user_lat: float, user_lng: float, max_distance: int = 5) -> List[Dict]:
        """Get nearby bars"""
        nearby_bars = []
        user_coords = (user_lat, user_lng)
        
        for bar in self.bars_data:
            bar_coords = (bar['lat'], bar['lng'])
            distance = self.calculate_distance(user_coords, bar_coords)
            
            if distance <= max_distance:
                bar_copy = bar.copy()
                bar_copy['distance'] = distance
                nearby_bars.append(bar_copy)
        
        return sorted(nearby_bars, key=lambda x: x['distance'])
    
    def generate_ai_description(self, bar_name: str, vibe: str) -> str:
        """Generate AI description"""
        openai_key = get_openai_key()
        if not openai_key:
            return vibe
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Write sophisticated, concise rooftop bar descriptions in 2-3 sentences."},
                    {"role": "user", "content": f"Describe {bar_name}: {vibe}"}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except:
            return vibe
    
    def create_map(self, user_lat: float, user_lng: float, nearby_bars: List[Dict]):
        """Create professional map"""
        m = folium.Map(
            location=[user_lat, user_lng],
            zoom_start=13,
            tiles=None
        )
        
        # Dark theme
        folium.TileLayer(
            tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            attr='CartoDB',
            name="Dark Theme"
        ).add_to(m)
        
        # User marker
        folium.Marker(
            [user_lat, user_lng],
            popup="📍 Your Location",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)
        
        # Bar markers
        for i, bar in enumerate(nearby_bars):
            color = 'blue' if i < 3 else 'green' if i < 6 else 'purple'
            
            folium.Marker(
                [bar['lat'], bar['lng']],
                popup=f"#{i+1} {bar['name']}\n⭐ {bar.get('rating', 'N/A')}/5\n📏 {bar['distance']:.1f}mi",
                tooltip=f"#{i+1} {bar['name']}",
                icon=folium.Icon(color=color, icon='glass')
            ).add_to(m)
        
        return m

def render_bar_card_native(bar: Dict, index: int):
    """Render bar card using ONLY Streamlit native components"""
    links = finder.generate_bar_links(bar)
    
    # Create container with custom styling
    with st.container():
        # Card header with ranking
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {bar['name']}")
        with col2:
            st.markdown(f"**#{index + 1}**")
        
        # Metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📍 Location", bar.get('neighborhood', 'NYC'))
        
        with col2:
            rating = bar.get('rating', 0)
            st.metric("⭐ Rating", f"{rating}/5" if rating else "N/A")
        
        with col3:
            st.metric("💰 Price", bar.get('price_range', '$$'))
        
        with col4:
            if 'distance' in bar:
                st.metric("🚶 Distance", f"{bar['distance']:.1f} mi")
        
        # Description
        st.markdown(f"*\"{bar['vibe']}\"*")
        
        # Action buttons using columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"[📱 **Yelp**]({links['yelp']})")
        with col2:
            st.markdown(f"[🗺️ **Directions**]({links['maps']})")
        with col3:
            st.markdown(f"[🍽️ **Reserve**]({links['opentable']})")
        
        st.divider()  # Clean separator

def main():
    global finder
    finder = RooftopBarFinder()
    
    # Professional Header using native Streamlit
    st.markdown("""
    <div class="custom-header">
        <h1 class="main-title">Elevate NYC</h1>
        <p class="subtitle">Discover the city's finest rooftop experiences</p>
        <p class="tagline">Curated • Premium • Elevated</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search Interface using native components
    st.markdown('<div class="search-card">', unsafe_allow_html=True)
    st.subheader("🔍 Find Your Perfect Rooftop")
    
    # Search controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        selected_borough = st.selectbox(
            "Borough",
            options=list(finder.nyc_neighborhoods.keys()),
            index=0
        )
    
    with col2:
        selected_neighborhood = st.selectbox(
            "Neighborhood",
            options=finder.nyc_neighborhoods[selected_borough]
        )
    
    with col3:
        max_distance = st.selectbox(
            "Radius",
            options=[0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 7, 10],
            index=3,  # This selects 2 miles as default (0-indexed: 0.5, 1, 1.5, 2)
            format_func=lambda x: f"{x} mi"
        )
    
    # Search button
    search_button = st.button("🚀 Discover Rooftops", type="primary")
    
    # Advanced filters
    with st.expander("🎛️ Advanced Filters"):
        col1, col2 = st.columns(2)
        
        with col1:
            price_filter = st.multiselect(
                "Price Range",
                options=["$", "$$", "$$$", "$$$$"],
                default=["$", "$$", "$$$", "$$$$"]
            )
        
        with col2:
            min_rating = st.slider(
                "Minimum Rating",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.1
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Search Logic
    if search_button:
        with st.spinner(f"🔍 Finding rooftops near {selected_neighborhood}..."):
            user_lat, user_lng = finder.get_neighborhood_center(selected_neighborhood, selected_borough)
            
            if user_lat and user_lng:
                nearby_bars = finder.get_bars_nearby(user_lat, user_lng, max_distance)
                
                # Apply filters
                filtered_bars = [
                    bar for bar in nearby_bars 
                    if bar.get('price_range', '$$') in price_filter 
                    and bar.get('rating', 0) >= min_rating
                ]
                
                if filtered_bars:
                    st.session_state.search_results = filtered_bars
                    st.session_state.user_location = (user_lat, user_lng)
                    st.session_state.search_location = f"{selected_neighborhood}, {selected_borough}"
                    st.session_state.search_performed = True
                    
                    st.success(f"✨ Found {len(filtered_bars)} exceptional venues!")
                else:
                    st.warning("🔍 No venues match your criteria. Try adjusting filters.")
            else:
                st.error("📍 Unable to locate neighborhood. Please try another area.")
    
    # Display Results
    if st.session_state.search_results and st.session_state.search_performed:
        nearby_bars = st.session_state.search_results
        user_lat, user_lng = st.session_state.user_location
        
        # Results layout
        col1, col2 = st.columns([1.6, 1.4], gap="large")
        
        with col1:
            st.subheader(f"📍 {st.session_state.get('search_location', 'Results')}")
            map_obj = finder.create_map(user_lat, user_lng, nearby_bars)
            st_folium(map_obj, width="100%", height=500)
        
        with col2:
            st.subheader("🏆 Top Recommendations")
            
            for i, bar in enumerate(nearby_bars[:8]):
                ai_description = finder.generate_ai_description(bar['name'], bar['vibe'])
                bar_with_ai = bar.copy()
                bar_with_ai['vibe'] = ai_description
                render_bar_card_native(bar_with_ai, i)
        
        # New search button
        if st.button("🔄 Search New Area"):
            st.session_state.search_results = None
            st.session_state.user_location = None
            st.session_state.search_performed = False
            st.rerun()
    
    # Featured Section
    elif not st.session_state.search_performed:
        st.subheader("🌟 Featured Rooftop Experiences")
        st.write("*Discover NYC's most exceptional rooftop venues*")
        
        if finder.bars_data:
            featured_bars = sorted(finder.bars_data, key=lambda x: x.get('rating', 0), reverse=True)[:6]
            
            col1, col2 = st.columns(2)
            
            for i, bar in enumerate(featured_bars):
                with col1 if i % 2 == 0 else col2:
                    ai_description = finder.generate_ai_description(bar['name'], bar['vibe'])
                    bar_with_ai = bar.copy()
                    bar_with_ai['vibe'] = ai_description
                    render_bar_card_native(bar_with_ai, i)

if __name__ == "__main__":
    main()