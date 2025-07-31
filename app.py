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

def check_api_keys():
    """Check if API keys are available and warn if missing"""
    if not os.getenv("OPENAI_API_KEY"):
        st.sidebar.info("""
        💡 **Enhanced Descriptions Available**
        
        Add your OpenAI API key in Streamlit Cloud secrets 
        for AI-powered bar descriptions!
        
        The app works perfectly without it.
        """)

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Elevate NYC | Rooftop Bar Finder",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="auto"
)
check_api_keys()

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'user_location' not in st.session_state:
    st.session_state.user_location = None

# Professional Dark Theme CSS - Streamlined
st.markdown("""
<style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap');
    
    /* Global Dark Theme */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Professional Header */
    .hero-header {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #e5e7eb;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    .tagline {
        color: #9ca3af;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #1a1a1a;
        border-right: 1px solid #374151;
    }
    
    /* Professional Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        filter: brightness(1.1);
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background-color: #262626;
        border: 1px solid #374151;
        border-radius: 8px;
        color: white;
    }
    
    /* Slider styling */
    .stSlider > div > div > div > div {
        color: #667eea;
    }
    
    /* Metric styling */
    .metric-container {
        background: #262626;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #374151;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid #10b981 !important;
        color: #10b981 !important;
        border-radius: 8px !important;
    }
    
    .stError {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid #ef4444 !important;
        color: #ef4444 !important;
        border-radius: 8px !important;
    }
    
    .stWarning {
        background-color: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid #f59e0b !important;
        color: #f59e0b !important;
        border-radius: 8px !important;
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem !important;
        }
        .subtitle {
            font-size: 1rem !important;
        }
    }
    
    /* Custom spacing */
    .stContainer > div {
        padding-top: 1rem;
    }
    
    /* Map container */
    .map-container {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        border: 1px solid #374151;
    }
</style>
""", unsafe_allow_html=True)

class RooftopBarFinder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="elevate_nyc_finder")
        if os.getenv("OPENAI_API_KEY"):
            openai.api_key = os.getenv("OPENAI_API_KEY")
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
        if not os.getenv("OPENAI_API_KEY"):
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
                tooltip=f"{bar['name']} • {bar['distance']:.1f}mi",
                icon=folium.Icon(color=color, icon='glass')
            ).add_to(m)
        
        return m

def render_bar_card_streamlit(bar: Dict, index: int):
    """Render bar card using Streamlit components"""
    links = finder.generate_bar_links(bar)
    
    # Container with custom styling
    with st.container():
        st.markdown(f"""
        <div style="
            background: #262626;
            border: 1px solid #374151;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        ">
        """, unsafe_allow_html=True)
        
        # Header with ranking
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {bar['name']}")
        with col2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 0.3rem 0.6rem;
                border-radius: 20px;
                text-align: center;
                font-weight: 600;
                font-size: 0.9rem;
            ">#{index + 1}</div>
            """, unsafe_allow_html=True)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📍 Location", f"{bar.get('neighborhood', 'NYC')}")
        
        with col2:
            rating = bar.get('rating', 0)
            stars = "⭐" * int(rating) if rating else "N/A"
            st.metric("Rating", f"{rating}/5" if rating else "N/A")
        
        with col3:
            st.metric("💰 Price", bar.get('price_range', '$$'))
        
        with col4:
            if 'distance' in bar:
                st.metric("🚶 Distance", f"{bar['distance']:.1f} mi")
        
        # Description
        st.markdown(f"*\"{bar['vibe']}\"*")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"[📱 Yelp]({links['yelp']})")
        with col2:
            st.markdown(f"[🗺️ Directions]({links['maps']})")
        with col3:
            st.markdown(f"[🍽️ Reserve]({links['opentable']})")
        
        st.markdown("</div>", unsafe_allow_html=True)

def main():
    global finder
    finder = RooftopBarFinder()
    
    # Professional Header
    st.markdown("""
    <div class="hero-header">
        <h1 class="main-title">Elevate NYC</h1>
        <p class="subtitle">Discover the city's finest rooftop experiences</p>
        <p class="tagline">Curated • Premium • Elevated</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🏙️ Location Selection")
        
        selected_borough = st.selectbox(
            "Borough:",
            options=list(finder.nyc_neighborhoods.keys()),
            index=0
        )
        
        selected_neighborhood = st.selectbox(
            "Neighborhood:",
            options=finder.nyc_neighborhoods[selected_borough]
        )
        
        st.markdown("---")
        st.markdown("## ⚙️ Search Parameters")
        
        max_distance = st.slider(
            "Search radius (miles):",
            min_value=1,
            max_value=15,
            value=5,
            step=1
        )
        
        search_button = st.button("🔍 Discover Rooftops", type="primary")
        
        st.markdown("---")
        st.markdown("## 🎛️ Filters")
        
        price_filter = st.multiselect(
            "Price Range:",
            options=["$", "$$", "$$$", "$$$$"],
            default=["$", "$$", "$$$", "$$$$"]
        )
        
        min_rating = st.slider(
            "Minimum Rating:",
            min_value=1.0,
            max_value=5.0,
            value=3.0,
            step=0.1
        )
        
        if st.session_state.search_results:
            if st.button("🔄 New Search"):
                st.session_state.search_results = None
                st.session_state.user_location = None
                st.rerun()
    
    # Search Logic
    if search_button:
        with st.spinner(f"🔍 Finding rooftop experiences near {selected_neighborhood}..."):
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
                    
                    st.success(f"✨ Found {len(filtered_bars)} exceptional rooftop venues!")
                else:
                    st.warning("🔍 No venues match your criteria. Try adjusting filters.")
            else:
                st.error("📍 Unable to locate neighborhood. Please try another selection.")
    
    # Display Results
    if st.session_state.search_results:
        nearby_bars = st.session_state.search_results
        user_lat, user_lng = st.session_state.user_location
        
        # Two-column layout
        col1, col2 = st.columns([1.8, 1.2])
        
        with col1:
            st.subheader(f"📍 {st.session_state.get('search_location', 'Search Results')}")
            
            # Create map
            map_obj = finder.create_map(user_lat, user_lng, nearby_bars)
            
            # Display map with container styling
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st_folium(map_obj, width="100%", height=600, key="results_map")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.subheader("🏆 Curated Selection")
            
            # Display bars using Streamlit components
            for i, bar in enumerate(nearby_bars):
                ai_description = finder.generate_ai_description(bar['name'], bar['vibe'])
                bar_with_ai = bar.copy()
                bar_with_ai['vibe'] = ai_description
                render_bar_card_streamlit(bar_with_ai, i)
    
    # Featured Section
    else:
        st.subheader("🌟 Featured Rooftop Experiences")
        st.write("Select a neighborhood above to discover curated venues")
        
        if finder.bars_data:
            featured_bars = sorted(finder.bars_data, key=lambda x: x.get('rating', 0), reverse=True)[:6]
            
            # Display featured bars in columns
            col1, col2 = st.columns(2)
            
            for i, bar in enumerate(featured_bars):
                with col1 if i % 2 == 0 else col2:
                    render_bar_card_streamlit(bar, i)

if __name__ == "__main__":
    main()