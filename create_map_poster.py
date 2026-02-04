import osmnx as ox
from cache_manager import get_cache_manager

cache = get_cache_manager()
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim
from tqdm import tqdm
import time
import json
import os
from datetime import datetime
import argparse

THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "posters"

def load_fonts():
    """
    Load Roboto fonts from the fonts directory.
    Returns dict with font paths for different weights.
    """
    fonts = {
        'bold': os.path.join(FONTS_DIR, 'Roboto-Bold.ttf'),
        'regular': os.path.join(FONTS_DIR, 'Roboto-Regular.ttf'),
        'light': os.path.join(FONTS_DIR, 'Roboto-Light.ttf')
    }
    
    # Verify fonts exist
    for weight, path in fonts.items():
        if not os.path.exists(path):
            print(f"⚠ Font not found: {path}")
            return None
    
    return fonts

FONTS = load_fonts()

def generate_output_filename(city, theme_name):
    """
    Generate unique output filename with city, theme, and datetime.
    """
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    filename = f"{city_slug}_{theme_name}_{timestamp}.png"
    return os.path.join(POSTERS_DIR, filename)

def get_available_themes():
    """
    Scans the themes directory and returns a list of available theme names.
    """
    if not os.path.exists(THEMES_DIR):
        os.makedirs(THEMES_DIR)
        return []
    
    themes = []
    for file in sorted(os.listdir(THEMES_DIR)):
        if file.endswith('.json'):
            theme_name = file[:-5]  # Remove .json extension
            themes.append(theme_name)
    return themes

def load_theme(theme_name="feature_based"):
    """
    Load theme from JSON file in themes directory.
    """
    theme_path = os.path.join(THEMES_DIR, f"{theme_name}.json")
    
    if not os.path.exists(theme_path):
        print(f"⚠ Theme '{theme_name}' not found. Using default 'feature_based' theme.")
        theme_path = os.path.join(THEMES_DIR, "feature_based.json")
        
        if not os.path.exists(theme_path):
            print(f"✗ Default theme not found. Please ensure themes exist in {THEMES_DIR}")
            return None
    
    try:
        with open(theme_path, 'r') as f:
            theme_data = json.load(f)
        return theme_data
    except Exception as e:
        print(f"✗ Error loading theme: {e}")
        return None

def get_coordinates(city, country):
    """
    Get coordinates for a city with caching support.
    """
    # Try cache first
    cached_coords = cache.get_geocoding(city, country)
    if cached_coords is not None:
        print(f"✓ Using cached coordinates for {city}, {country}")
        return cached_coords
    
    # Cache miss - fetch from Nominatim
    print(f"⊙ Fetching coordinates for {city}, {country}...")
    geolocator = Nominatim(user_agent="map_poster_generator")
    
    try:
        location = geolocator.geocode(f"{city}, {country}")
        if location:
            coords = (location.latitude, location.longitude)
            # Cache the result
            cache.set_geocoding(city, country, coords[0], coords[1])
            print(f"✓ Cached coordinates for {city}, {country}")
            return coords
        else:
            print(f"✗ Could not find coordinates for {city}, {country}")
            return None
    except Exception as e:
        print(f"✗ Geocoding error: {e}")
        return None

def get_edge_colors_by_type(G, THEME):
    """
    Assign colors to edges based on road type hierarchy.
    """
    edge_colors = []
    
    for u, v, k, data in G.edges(keys=True, data=True):
        highway_type = data.get('highway', 'default')
        
        if isinstance(highway_type, list):
            highway_type = highway_type[0]
        
        if highway_type in ['motorway', 'motorway_link', 'trunk']:
            color = THEME['road_motorway']
        elif highway_type in ['primary', 'primary_link']:
            color = THEME['road_primary']
        elif highway_type in ['secondary', 'secondary_link']:
            color = THEME['road_secondary']
        elif highway_type in ['tertiary', 'tertiary_link']:
            color = THEME['road_tertiary']
        elif highway_type in ['residential', 'living_street']:
            color = THEME['road_residential']
        else:
            color = THEME['road_default']
        
        edge_colors.append(color)
    
    return edge_colors

def get_edge_widths_by_type(G):
    """
    Assign line widths based on road importance.
    """
    edge_widths = []
    
    for u, v, k, data in G.edges(keys=True, data=True):
        highway_type = data.get('highway', 'default')
        
        if isinstance(highway_type, list):
            highway_type = highway_type[0]
        
        if highway_type in ['motorway', 'motorway_link']:
            width = 1.2
        elif highway_type in ['trunk', 'primary']:
            width = 1.0
        elif highway_type in ['secondary']:
            width = 0.8
        elif highway_type in ['tertiary']:
            width = 0.6
        elif highway_type in ['residential', 'living_street']:
            width = 0.4
        else:
            width = 0.5
        
        edge_widths.append(width)
    
    return edge_widths

def create_gradient_fade(ax, THEME, height_fraction=0.15):
    """
    Add gradient fade at top and bottom of the poster.
    """
    gradient = np.linspace(0, 1, 256).reshape(256, 1)
    gradient = np.hstack([gradient] * 100)
    
    bg_color = mcolors.to_rgba(THEME['bg'])
    grad_color = mcolors.to_rgba(THEME.get('gradient_color', THEME['bg']))
    
    cmap_top = mcolors.LinearSegmentedColormap.from_list(
        'fade_top', [grad_color, bg_color]
    )
    cmap_bottom = mcolors.LinearSegmentedColormap.from_list(
        'fade_bottom', [bg_color, grad_color]
    )
    
    # Top fade
    ax.imshow(gradient, extent=[0, 1, 1-height_fraction, 1], 
              aspect='auto', cmap=cmap_top, alpha=0.6,
              transform=ax.transAxes, zorder=10)
    
    # Bottom fade
    ax.imshow(np.flipud(gradient), extent=[0, 1, 0, height_fraction],
              aspect='auto', cmap=cmap_bottom, alpha=0.6,
              transform=ax.transAxes, zorder=10)

def create_poster(city, country, theme_name='feature_based', distance=29000, 
                 width=16, height=20, dpi=500):
    """
    Create a map poster with caching support for OSM data.
    """
    print(f"\n{'='*60}")
    print(f"Creating poster for {city}, {country}")
    print(f"Theme: {theme_name}")
    print(f"Distance: {distance}m")
    print(f"{'='*60}\n")
    
    # Load theme
    THEME = load_theme(theme_name)
    if THEME is None:
        print("✗ Failed to load theme. Exiting.")
        return None
    
    # Get coordinates (with caching)
    coords = get_coordinates(city, country)
    if coords is None:
        print("✗ Failed to get coordinates. Exiting.")
        return None
    
    latitude, longitude = coords
    point = (latitude, longitude)
    
    print(f"📍 Coordinates: {latitude:.4f}, {longitude:.4f}")
    
    # Check OSM cache first
    print(f"\n⊙ Checking OSM data cache...")
    cached_osm = cache.get_osm_data(latitude, longitude, distance, 'all')
    
    if cached_osm is not None:
        print(f"✓ Using cached OSM data for {city}")
        G = cached_osm['graph']
        water = cached_osm['water']
        parks = cached_osm['parks']
    else:
        # Cache miss - fetch from OSM (slow!)
        print(f"⊙ Fetching OSM data for {city}...")
        print(f"   This may take 30-60 seconds for the first time...")
        
        # Fetch graph
        print("   → Fetching street network...")
        try:
            G = ox.graph_from_point(
                point, 
                dist=distance, 
                dist_type='bbox',
                network_type='all',
                truncate_by_edge=True
            )
            print(f"   ✓ Graph: {len(G.nodes)} nodes, {len(G.edges)} edges")
        except Exception as e:
            print(f"   ✗ Error fetching graph: {e}")
            G = None
        
        # Fetch water features
        print("   → Fetching water features...")
        try:
            water = ox.features_from_point(
                point,
                tags={'natural': 'water'},
                dist=distance
            )
            if water is not None and not water.empty:
                print(f"   ✓ Water: {len(water)} features")
            else:
                print(f"   ℹ No water features found")
                water = None
        except Exception as e:
            print(f"   ℹ No water features: {e}")
            water = None
        
        # Fetch parks
        print("   → Fetching parks...")
        try:
            parks = ox.features_from_point(
                point,
                tags={'leisure': 'park'},
                dist=distance
            )
            if parks is not None and not parks.empty:
                print(f"   ✓ Parks: {len(parks)} features")
            else:
                print(f"   ℹ No parks found")
                parks = None
        except Exception as e:
            print(f"   ℹ No parks: {e}")
            parks = None
        
        # Cache the OSM data for next time
        print(f"\n✓ Caching OSM data for future use...")
        cache.set_osm_data(latitude, longitude, distance, 'all', G, water, parks)
    
    if G is None:
        print("✗ No graph data available. Cannot create poster.")
        return None
    
    # Create figure
    print(f"\n🎨 Rendering poster...")
    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
    fig.patch.set_facecolor(THEME['bg'])
    ax.set_facecolor(THEME['bg'])
    
    # Plot water features (if any)
    if water is not None and not water.empty:
        try:
            water.plot(ax=ax, color=THEME['water'], zorder=1)
        except:
            pass
    
    # Plot parks (if any)
    if parks is not None and not parks.empty:
        try:
            parks.plot(ax=ax, color=THEME['parks'], zorder=2)
        except:
            pass
    
    # Plot street network
    edge_colors = get_edge_colors_by_type(G, THEME)
    edge_widths = get_edge_widths_by_type(G)
    
    ox.plot_graph(
        G, ax=ax,
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        bgcolor=THEME['bg'],
        show=False,
        close=False
    )
    
    # Add gradient fades
    create_gradient_fade(ax, THEME)
    
    # Add text labels
    if FONTS:
        font_bold = FontProperties(fname=FONTS['bold'])
        font_regular = FontProperties(fname=FONTS['regular'])
        font_light = FontProperties(fname=FONTS['light'])
        
        # City name (spaced letters)
        city_spaced = '  '.join(city.upper())
        ax.text(0.5, 0.14, city_spaced,
                fontproperties=font_bold,
                fontsize=32,
                color=THEME['text'],
                ha='center',
                va='center',
                transform=ax.transAxes,
                zorder=11)
        
        # Decorative line
        ax.plot([0.3, 0.7], [0.125, 0.125],
                color=THEME['text'],
                linewidth=1,
                transform=ax.transAxes,
                zorder=11)
        
        # Country name
        ax.text(0.5, 0.10, country.upper(),
                fontproperties=font_light,
                fontsize=14,
                color=THEME['text'],
                ha='center',
                va='center',
                transform=ax.transAxes,
                zorder=11)
        
        # Coordinates
        coord_text = f"{latitude:.4f}°N  {abs(longitude):.4f}°{'E' if longitude >= 0 else 'W'}"
        ax.text(0.5, 0.07, coord_text,
                fontproperties=font_light,
                fontsize=10,
                color=THEME['text'],
                ha='center',
                va='center',
                transform=ax.transAxes,
                zorder=11)
        
        # Attribution
        ax.text(0.95, 0.02, 'BlueBearLabs',
                fontproperties=font_light,
                fontsize=8,
                color=THEME['text'],
                ha='right',
                va='bottom',
                alpha=0.6,
                transform=ax.transAxes,
                zorder=11)
    
    # Remove axes
    ax.set_axis_off()
    ax.margins(0)
    
    # Save
    output_file = generate_output_filename(city, theme_name)
    print(f"💾 Saving to {output_file}...")
    
    plt.savefig(
        output_file,
        dpi=dpi,
        bbox_inches='tight',
        facecolor=THEME['bg'],
        edgecolor='none',
        pad_inches=0.1
    )
    plt.close()
    
    print(f"\n✅ Poster created successfully!")
    print(f"📁 Saved to: {output_file}")
    print(f"{'='*60}\n")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(
        description='Generate beautiful minimalist map posters',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-c', '--city', required=True,
                       help='City name (e.g., "Paris", "New York")')
    parser.add_argument('-C', '--country', required=True,
                       help='Country name (e.g., "France", "USA")')
    parser.add_argument('-t', '--theme', default='feature_based',
                       help='Theme name (default: feature_based)')
    parser.add_argument('-d', '--distance', type=int, default=29000,
                       help='Map radius in meters (default: 29000)')
    parser.add_argument('--width', type=int, default=16,
                       help='Poster width in inches (default: 16)')
    parser.add_argument('--height', type=int, default=20,
                       help='Poster height in inches (default: 20)')
    parser.add_argument('--dpi', type=int, default=500,
                       help='Resolution in DPI (default: 300)')
    parser.add_argument('--list-themes', action='store_true',
                       help='List all available themes')
    
    # Cache management arguments
    parser.add_argument('--cache-stats', action='store_true',
                       help='Show cache statistics')
    parser.add_argument('--clear-cache', choices=['all', 'geocoding', 'osm', 'posters'],
                       help='Clear cache')
    parser.add_argument('--cleanup-expired', action='store_true',
                       help='Remove expired cache files')
    
    args = parser.parse_args()
    
    # Handle cache commands
    if args.cache_stats:
        stats = cache.get_cache_stats()
        print("\n" + "="*60)
        print("CACHE STATISTICS")
        print("="*60)
        print(f"Geocoding: {stats['geocoding']['count']:>4} files, {stats['geocoding']['size_mb']:>8.2f} MB")
        print(f"OSM Data:  {stats['osm_data']['count']:>4} files, {stats['osm_data']['size_mb']:>8.2f} MB")
        print(f"Posters:   {stats['posters']['count']:>4} files, {stats['posters']['size_mb']:>8.2f} MB")
        print("-"*60)
        print(f"Total:     {stats['total_size_mb']:>8.2f} MB")
        print("="*60 + "\n")
        return
    
    if args.cleanup_expired:
        removed = cache.cleanup_expired()
        print(f"\n✓ Removed {removed} expired cache files\n")
        return
    
    if args.clear_cache:
        cache.clear_cache(args.clear_cache)
        print(f"\n✓ Cleared {args.clear_cache} cache\n")
        return
    
    # List themes
    if args.list_themes:
        themes = get_available_themes()
        print("\nAvailable themes:")
        print("="*60)
        for theme in themes:
            print(f"  • {theme}")
        print("="*60 + "\n")
        return
    
    # Create poster
    create_poster(
        city=args.city,
        country=args.country,
        theme_name=args.theme,
        distance=args.distance,
        width=args.width,
        height=args.height,
        dpi=args.dpi
    )

if __name__ == "__main__":
    main()
