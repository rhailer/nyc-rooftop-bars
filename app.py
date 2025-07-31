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

# Configure page - Mobile optimized
st.set_page_config(
    page_title="Elevate NYC | Rooftop Bar Finder",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",  # Start collapsed for mobile
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

# Professional Mobile-First CSS - Perplexity Inspired
st.markdown("""
<style>
    /* Import Premium Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=SF+Pro+Display:wght@400;500;600;700&display=swap');
    
    /* CSS Variables - Perplexity Inspired Color System */
    :root {
        --primary-bg: #0f0f0f;
        --secondary-bg: #1a1a1a;
        --card-bg: #202020;
        --accent-color: #2d7ff9;
        --accent-hover: #1e5fcc;
        --text-primary: #ffffff;
        --text-secondary: #b4b4b4;
        --text-muted: #6b7280;
        --border-color: #2d2d2d;
        --success-color: #00c896;
        --warning-color: #ffb000;
        --error-color: #ff4757;
        --gradient-primary: linear-gradient(135deg, #2d7ff9 0%, #1e40af 100%);
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.2);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.15);
        --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.2);
        --border-radius: 12px;
        --border-radius-lg: 16px;
        --spacing-xs: 0.5rem;
        --spacing-sm: 0.75rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
    }
    
    /* Global Reset and Base Styles */
    .stApp {
        background: var(--primary-bg);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        line-height: 1.6;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* Main Container Spacing */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Professional Header - Centered, Clean */
    .hero-section {
        text-align: center;
        padding: var(--spacing-xl) var(--spacing-md);
        margin-bottom: var(--spacing-xl);
        background: var(--card-bg);
        border-radius: var(--border-radius-lg);
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-md);
    }
    
    .main-title {
        font-family: 'SF Pro Display', 'Inter', sans-serif;
        font-size: 2.75rem;
        font-weight: 700;
        background: var(--gradient-primary);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: var(--spacing-xs);
        letter-spacing: -0.025em;
    }
    
    .subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: var(--spacing-xs);
    }
    
    .tagline {
        color: var(--text-muted);
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Search Section - Mobile First */
    .search-section {
        background: var(--card-bg);
        border-radius: var(--border-radius-lg);
        border: 1px solid var(--border-color);
        padding: var(--spacing-lg);
        margin-bottom: var(--spacing-xl);
        box-shadow: var(--shadow-md);
    }
    
    .search-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-md);
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
    }
    
    /* Professional Form Controls */
    .stSelectbox > div > div {
        background: var(--secondary-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--border-radius) !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 3px rgba(45, 127, 249, 0.1) !important;
    }
    
    /* Slider Styling */
    .stSlider > div > div > div {
        background: var(--secondary-bg);
    }
    
    .stSlider > div > div > div > div {
        background: var(--accent-color) !important;
    }
    
    /* Professional Buttons - Perplexity Style */
    .stButton > button {
        background: var(--gradient-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--border-radius) !important;
        padding: var(--spacing-sm) var(--spacing-lg) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        box-shadow: var(--shadow-sm) !important;
        height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
        filter: brightness(1.05) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Results Cards - High Contrast */
    .bar-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-lg);
        margin-bottom: var(--spacing-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-sm);
        position: relative;
        overflow: hidden;
    }
    
    .bar-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--gradient-primary);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .bar-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-color);
    }
    
    .bar-card:hover::before {
        opacity: 1;
    }
    
    /* Card Header - Improved Contrast */
    .bar-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: var(--spacing-md);
        gap: var(--spacing-sm);
    }
    
    .bar-name {
        font-family: 'SF Pro Display', 'Inter', sans-serif;
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--text-primary);  /* Pure white for maximum contrast */
        margin: 0;
        flex: 1;
        line-height: 1.3;
    }
    
    .bar-ranking {
        background: var(--gradient-primary);
        color: white;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        min-width: 35px;
        text-align: center;
        flex-shrink: 0;
    }
    
    /* Metrics Row - Clean Layout */
    .bar-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: var(--spacing-sm);
        margin-bottom: var(--spacing-md);
        padding: var(--spacing-sm);
        background: var(--secondary-bg);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    .metric-item {
        text-align: center;
        padding: var(--spacing-xs);
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    
    .metric-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .metric-value.rating {
        color: #fbbf24;
    }
    
    .metric-value.price {
        color: var(--accent-color);
    }
    
    .metric-value.distance {
        color: var(--success-color);
    }
    
    /* Description - Better Contrast */
    .bar-description {
        color: var(--text-secondary);  /* Lighter gray for better readability */
        font-style: italic;
        line-height: 1.5;
        margin-bottom: var(--spacing-md);
        padding: var(--spacing-sm);
        background: rgba(255, 255, 255, 0.02);
        border-radius: var(--border-radius);
        border-left: 3px solid var(--accent-color);
    }
    
    /* Action Buttons */
    .action-buttons {
        display: flex;
        gap: var(--spacing-xs);
        flex-wrap: wrap;
    }
    
    .action-link {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: var(--spacing-xs) var(--spacing-sm);
        background: rgba(45, 127, 249, 0.1);
        border: 1px solid rgba(45, 127, 249, 0.2);
        border-radius: var(--border-radius);
        color: var(--accent-color);
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: 500;
        transition: all 0.2s ease;
        flex: 1;
        justify-content: center;
        min-width: 80px;
    }
    
    .action-link:hover {
        background: rgba(45, 127, 249, 0.2);
        border-color: var(--accent-color);
        text-decoration: none;
        color: var(--accent-color);
        transform: translateY(-1px);
    }
    
    .action-link.primary {
        background: var(--gradient-primary);
        border-color: transparent;
        color: white;
    }
    
    .action-link.primary:hover {
        filter: brightness(1.1);
        color: white;
    }
    
    /* Map Container */
    .map-container {
        border-radius: var(--border-radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
        background: var(--card-bg);
        margin-bottom: var(--spacing-lg);
    }
    
    .map-header {
        background: var(--card-bg);
        padding: var(--spacing-md);
        border-bottom: 1px solid var(--border-color);
    }
    
    .map-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        display: flex;
        align-items: center;
        gap: var(--spacing-xs);
    }
    
    /* Status Messages - High Contrast */
    .stSuccess {
        background: rgba(0, 200, 150, 0.1) !important;
        border: 1px solid var(--success-color) !important;
        color: var(--success-color) !important;
        border-radius: var(--border-radius) !important;
    }
    
    .stError {
        background: rgba(255, 71, 87, 0.1) !important;
        border: 1px solid var(--error-color) !important;
        color: var(--error-color) !important;
        border-radius: var(--border-radius) !important;
    }
    
    .stWarning {
        background: rgba(255, 176, 0, 0.1) !important;
        border: 1px solid var(--warning-color) !important;
        color: var(--warning-color) !important;
        border-radius: var(--border-radius) !important;
    }
    
    /* Mobile Responsive Breakpoints */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.25rem !important;
        }
        
        .subtitle {
            font-size: 1rem !important;
        }
        
        .bar-header {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--spacing-xs);
        }
        
        .bar-ranking {
            align-self: flex-start;
        }
        
        .bar-metrics {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .action-buttons {
            flex-direction: column;
        }
        
        .action-link {
            flex: none;
        }
    }
    
    /* Loading States */
    .stSpinner > div {
        border-top-color: var(--accent-color) !important;
    }
    
    /* Expandable Filters */
    .filters-section {
        background: var(--secondary-bg);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        margin-top: var(--spacing-md);
        overflow: hidden;
    }
    
    .filters-header {
        padding: var(--spacing-sm) var(--spacing-md);
        background: var(--card-bg);
        border-bottom: 1px solid var(--border-color);
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--text-secondary);
    }
    
    .filters-content {
        padding: var(--spacing-md);
    }
    
    /* Multiselect Styling */
    .stMultiSelect > div > div {
        background: var(--secondary-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--border-radius) !important;
    }
    
    /* Featured Section */
    .featured-section {
        margin-top: var(--spacing-xl);
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-md);
        text-align: center;
    }
    
    .section-subtitle {
        color: var(--text-muted);
        text-align: center;
        margin-bottom: var(--spacing-lg);
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
                    {"role": "system", "content": "Write sophisticated, concise rooftop bar descriptions in 2-3 sentences. Focus on atmosphere and unique features."},
                    {"role": "user", "content": f"Describe {bar_name}, a NYC rooftop bar: {vibe}"}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except:
            return vibe
    
    def create_professional_map(self, user_lat: float, user_lng: float, nearby_bars: List[Dict]):
        """Create professional map"""
        m = folium.Map(
            location=[user_lat, user_lng],
            zoom_start=13,
            tiles=None
        )
        
        # Dark theme
        folium.TileLayer(
            tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            attr='&copy; OpenStreetMap contributors &copy; CARTO',
            name="Dark Theme"
        ).add_to(m)
        
        # User marker
        folium.Marker(
            [user_lat, user_lng],
            popup="📍 Your Location",
            tooltip="You are here",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)
        
        # Bar markers with ranking-based colors
        for i, bar in enumerate(nearby_bars):
            if i < 3:
                color = 'blue'
            elif i < 6:
                color = 'green'
            else:
                color = 'purple'
            
            folium.Marker(
                [bar['lat'], bar['lng']],
                popup=f"#{i+1} {bar['name']}\n⭐ {bar.get('rating', 'N/A')}/5\n📏 {bar['distance']:.1f}mi",
                tooltip=f"#{i+1} {bar['name']} • {bar['distance']:.1f}mi",
                icon=folium.Icon(color=color, icon='glass')
            ).add_to(m)
        
        return m

def render_bar_card(bar: Dict, index: int):
    """Render professional bar card with high contrast"""
    links = finder.generate_bar_links(bar)
    
    # Card container
    st.markdown(f"""
    <div class="bar-card">
        <div class="bar-header">
            <h3 class="bar-name">{bar['name']}</h3>
            <div class="bar-ranking">#{index + 1}</div>
        </div>
        
        <div class="bar-metrics">
            <div class="metric-item">
                <div class="metric-label">Location</div>
                <div class="metric-value">📍 {bar.get('neighborhood', 'NYC')}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">Rating</div>
                <div class="metric-value rating">⭐ {bar.get('rating', 'N/A')}/5</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">Price</div>
                <div class="metric-value price">💰 {bar.get('price_range', '$$')}</div>
            </div>
            {"<div class='metric-item'><div class='metric-label'>Distance</div><div class='metric-value distance'>🚶 " + f"{bar['distance']:.1f} mi</div></div>" if 'distance' in bar else ""}
        </div>
        
        <div class="bar-description">
            "{bar['vibe']}"
        </div>
        
        <div class="action-buttons">
            <a href="{links['yelp']}" target="_blank" class="action-link primary">
                📱 Yelp
            </a>
            <a href="{links['maps']}" target="_blank" class="action-link">
                🗺️ Directions
            </a>
            <a href="{links['opentable']}" target="_blank" class="action-link">
                🍽️ Reserve
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_search_interface():
    """Render the main search interface"""
    st.markdown("""
    <div class="search-section">
        <h2 class="search-header">🔍 Find Your Perfect Rooftop</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for the search interface
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        selected_borough = st.selectbox(
            "Borough",
            options=list(finder.nyc_neighborhoods.keys()),
            index=0,
            key="borough_select"
        )
    
    with col2:
        selected_neighborhood = st.selectbox(
            "Neighborhood",
            options=finder.nyc_neighborhoods[selected_borough],
            key="neighborhood_select"
        )
    
    with col3:
        max_distance = st.selectbox(
            "Radius",
            options=[1, 2, 3, 5, 7, 10],
            index=3,  # Default to 5 miles
            format_func=lambda x: f"{x} mi",
            key="distance_select"
        )
    
    # Search button - full width
    search_button = st.button("🚀 Discover Rooftops", type="primary", key="main_search")
    
    # Expandable filters
    with st.expander("🎛️ Advanced Filters", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            price_filter = st.multiselect(
                "Price Range",
                options=["$", "$$", "$$$", "$$$$"],
                default=["$", "$$", "$$$", "$$$$"],
                key="price_filter"
            )
        
        with col2:
            min_rating = st.slider(
                "Minimum Rating",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.1,
                key="rating_filter"
            )
    
    return selected_borough, selected_neighborhood, max_distance, search_button, price_filter, min_rating

def main():
    global finder
    finder = RooftopBarFinder()
    
    # Professional Header
    st.markdown("""
    <div class="hero-section">
        <h1 class="main-title">Elevate NYC</h1>
        <p class="subtitle">Discover the city's finest rooftop experiences</p>
        <p class="tagline">Curated • Premium • Elevated</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Search Interface - No Sidebar
    selected_borough, selected_neighborhood, max_distance, search_button, price_filter, min_rating = render_search_interface()
    
    # Search Logic
    if search_button:
        with st.spinner(f"🔍 Finding exceptional rooftops near {selected_neighborhood}..."):
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
                    
                    st.success(f"✨ Found {len(filtered_bars)} exceptional venues near {selected_neighborhood}!")
                else:
                    st.warning("🔍 No venues match your criteria. Try adjusting your filters.")
            else:
                st.error("📍 Unable to locate the selected neighborhood. Please try another area.")
    
    # Display Results
    if st.session_state.search_results and st.session_state.search_performed:
        nearby_bars = st.session_state.search_results
        user_lat, user_lng = st.session_state.user_location
        
        # Results layout - Mobile responsive
        col1, col2 = st.columns([1.6, 1.4], gap="large")
        
        with col1:
            # Map section
            st.markdown(f"""
            <div class="map-container">
                <div class="map-header">
                    <h3 class="map-title">📍 {st.session_state.get('search_location', 'Search Results')}</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            map_obj = finder.create_professional_map(user_lat, user_lng, nearby_bars)
            st_folium(map_obj, width="100%", height=500, key="results_map")
        
        with col2:
            # Results list
            st.markdown('<h3 class="section-title">🏆 Top Recommendations</h3>', unsafe_allow_html=True)
            
            # Display top results
            for i, bar in enumerate(nearby_bars[:8]):  # Limit to top 8 for performance
                ai_description = finder.generate_ai_description(bar['name'], bar['vibe'])
                bar_with_ai = bar.copy()
                bar_with_ai['vibe'] = ai_description
                render_bar_card(bar_with_ai, i)
        
        # New search button
        if st.button("🔄 Search New Area", key="new_search"):
            st.session_state.search_results = None
            st.session_state.user_location = None
            st.session_state.search_performed = False
            st.rerun()
    
    # Featured Section (when no search performed)
    elif not st.session_state.search_performed:
        st.markdown("""
        <div class="featured-section">
            <h2 class="section-title">🌟 Featured Rooftop Experiences</h2>
            <p class="section-subtitle">Discover NYC's most exceptional rooftop venues</p>
        </div>
        """, unsafe_allow_html=True)
        
        if finder.bars_data:
            # Show top-rated featured bars
            featured_bars = sorted(finder.bars_data, key=lambda x: x.get('rating', 0), reverse=True)[:6]
            
            # Display in responsive columns
            col1, col2 = st.columns(2, gap="medium")
            
            for i, bar in enumerate(featured_bars):
                with col1 if i % 2 == 0 else col2:
                    ai_description = finder.generate_ai_description(bar['name'], bar['vibe'])
                    bar_with_ai = bar.copy()
                    bar_with_ai['vibe'] = ai_description
                    render_bar_card(bar_with_ai, i)

if __name__ == "__main__":
    main()