"""
Caching module for MapToPoster
Caches geocoding results, OSM data, and optionally generated posters
"""
import os
import json
import hashlib
import pickle
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for geocoding, OSM data, and generated posters"""
    
    def __init__(self, cache_dir: str = "./cache"):
        """
        Initialize the cache manager
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.geocoding_dir = self.cache_dir / "geocoding"
        self.osm_dir = self.cache_dir / "osm_data"
        self.poster_dir = self.cache_dir / "posters"
        
        # Create cache directories
        for directory in [self.geocoding_dir, self.osm_dir, self.poster_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Cache expiration times (in days)
        self.geocoding_ttl = 90  # Coordinates rarely change
        self.osm_ttl = 7  # OSM data changes more frequently
        self.poster_ttl = 30  # Posters can be cached longer
        
        logger.info(f"Cache manager initialized at {self.cache_dir}")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_file: Path, ttl_days: int) -> bool:
        """Check if cache file exists and is not expired"""
        if not cache_file.exists():
            return False
        
        # Check file age
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - file_time
        
        if age > timedelta(days=ttl_days):
            logger.info(f"Cache expired: {cache_file.name}")
            return False
        
        return True
    
    # Geocoding Cache Methods
    
    def get_geocoding(self, city: str, country: str) -> Optional[Tuple[float, float]]:
        """
        Get cached geocoding result
        
        Args:
            city: City name
            country: Country name
            
        Returns:
            Tuple of (latitude, longitude) or None if not cached
        """
        cache_key = self._generate_key(city.lower(), country.lower())
        cache_file = self.geocoding_dir / f"{cache_key}.json"
        
        if self._is_cache_valid(cache_file, self.geocoding_ttl):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Geocoding cache HIT: {city}, {country}")
                return (data['latitude'], data['longitude'])
            except Exception as e:
                logger.error(f"Error reading geocoding cache: {e}")
                return None
        
        logger.info(f"Geocoding cache MISS: {city}, {country}")
        return None
    
    def set_geocoding(self, city: str, country: str, latitude: float, longitude: float):
        """
        Cache geocoding result
        
        Args:
            city: City name
            country: Country name
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        """
        cache_key = self._generate_key(city.lower(), country.lower())
        cache_file = self.geocoding_dir / f"{cache_key}.json"
        
        data = {
            'city': city,
            'country': country,
            'latitude': latitude,
            'longitude': longitude,
            'cached_at': datetime.now().isoformat()
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cached geocoding: {city}, {country}")
        except Exception as e:
            logger.error(f"Error caching geocoding: {e}")
    
    # OSM Data Cache Methods
    
    def get_osm_data(self, latitude: float, longitude: float, 
                     distance: int, network_type: str = 'all') -> Optional[Dict[str, Any]]:
        """
        Get cached OSM data
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            distance: Distance in meters
            network_type: Type of network ('all', 'drive', 'walk', etc.)
            
        Returns:
            Dictionary containing graph, water, and parks data, or None if not cached
        """
        # Round coordinates to 4 decimal places (~11m precision)
        lat_rounded = round(latitude, 4)
        lon_rounded = round(longitude, 4)
        
        cache_key = self._generate_key(lat_rounded, lon_rounded, distance, network_type)
        cache_file = self.osm_dir / f"{cache_key}.pkl"
        
        if self._is_cache_valid(cache_file, self.osm_ttl):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                logger.info(f"OSM data cache HIT: ({lat_rounded}, {lon_rounded}), dist={distance}")
                return data
            except Exception as e:
                logger.error(f"Error reading OSM cache: {e}")
                return None
        
        logger.info(f"OSM data cache MISS: ({lat_rounded}, {lon_rounded}), dist={distance}")
        return None
    
    def set_osm_data(self, latitude: float, longitude: float, distance: int,
                     network_type: str, graph, water, parks):
        """
        Cache OSM data
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            distance: Distance in meters
            network_type: Type of network
            graph: OSMnx graph object
            water: Water features GeoDataFrame
            parks: Parks GeoDataFrame
        """
        lat_rounded = round(latitude, 4)
        lon_rounded = round(longitude, 4)
        
        cache_key = self._generate_key(lat_rounded, lon_rounded, distance, network_type)
        cache_file = self.osm_dir / f"{cache_key}.pkl"
        
        data = {
            'graph': graph,
            'water': water,
            'parks': parks,
            'latitude': lat_rounded,
            'longitude': lon_rounded,
            'distance': distance,
            'network_type': network_type,
            'cached_at': datetime.now().isoformat()
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Cached OSM data: ({lat_rounded}, {lon_rounded}), dist={distance}")
        except Exception as e:
            logger.error(f"Error caching OSM data: {e}")
    
    # Poster Cache Methods (Optional)
    
    def get_poster(self, city: str, country: str, theme: str, 
                   distance: int, width: int, height: int, dpi: int) -> Optional[str]:
        """
        Get cached poster path
        
        Args:
            city, country, theme, distance, width, height, dpi: Poster parameters
            
        Returns:
            Path to cached poster or None if not cached
        """
        cache_key = self._generate_key(
            city.lower(), country.lower(), theme, distance, width, height, dpi
        )
        cache_file = self.poster_dir / f"{cache_key}.png"
        
        if self._is_cache_valid(cache_file, self.poster_ttl):
            logger.info(f"Poster cache HIT: {city}, {country}, {theme}")
            return str(cache_file)
        
        logger.info(f"Poster cache MISS: {city}, {country}, {theme}")
        return None
    
    def set_poster(self, poster_path: str, city: str, country: str, theme: str,
                   distance: int, width: int, height: int, dpi: int):
        """
        Cache a generated poster
        
        Args:
            poster_path: Path to the generated poster
            city, country, theme, distance, width, height, dpi: Poster parameters
        """
        cache_key = self._generate_key(
            city.lower(), country.lower(), theme, distance, width, height, dpi
        )
        cache_file = self.poster_dir / f"{cache_key}.png"
        
        try:
            shutil.copy2(poster_path, cache_file)
            logger.info(f"Cached poster: {city}, {country}, {theme}")
        except Exception as e:
            logger.error(f"Error caching poster: {e}")
    
    # Cache Management Methods
    
    def clear_cache(self, cache_type: str = 'all'):
        """
        Clear cache
        
        Args:
            cache_type: Type of cache to clear ('all', 'geocoding', 'osm', 'posters')
        """
        directories = {
            'all': [self.geocoding_dir, self.osm_dir, self.poster_dir],
            'geocoding': [self.geocoding_dir],
            'osm': [self.osm_dir],
            'posters': [self.poster_dir]
        }
        
        for directory in directories.get(cache_type, []):
            for file in directory.glob('*'):
                try:
                    file.unlink()
                    logger.info(f"Deleted cache file: {file}")
                except Exception as e:
                    logger.error(f"Error deleting {file}: {e}")
        
        logger.info(f"Cleared {cache_type} cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        def get_dir_stats(directory: Path) -> Dict[str, Any]:
            files = list(directory.glob('*'))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            return {
                'count': len(files),
                'size_mb': round(total_size / (1024 * 1024), 2)
            }
        
        return {
            'geocoding': get_dir_stats(self.geocoding_dir),
            'osm_data': get_dir_stats(self.osm_dir),
            'posters': get_dir_stats(self.poster_dir),
            'total_size_mb': round(
                sum(
                    get_dir_stats(d)['size_mb'] 
                    for d in [self.geocoding_dir, self.osm_dir, self.poster_dir]
                ), 2
            )
        }
    
    def cleanup_expired(self):
        """Remove expired cache files"""
        removed_count = 0
        
        # Clean geocoding cache
        for file in self.geocoding_dir.glob('*.json'):
            if not self._is_cache_valid(file, self.geocoding_ttl):
                file.unlink()
                removed_count += 1
        
        # Clean OSM cache
        for file in self.osm_dir.glob('*.pkl'):
            if not self._is_cache_valid(file, self.osm_ttl):
                file.unlink()
                removed_count += 1
        
        # Clean poster cache
        for file in self.poster_dir.glob('*.png'):
            if not self._is_cache_valid(file, self.poster_ttl):
                file.unlink()
                removed_count += 1
        
        logger.info(f"Removed {removed_count} expired cache files")
        return removed_count


# Global cache instance
_cache_manager = None

def get_cache_manager(cache_dir: str = "./cache") -> CacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir)
    return _cache_manager
