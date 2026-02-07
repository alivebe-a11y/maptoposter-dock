"""
Stadium database for MapToPoster
Contains coordinates and metadata for major sports stadiums
"""

STADIUMS = {
    # Premier League - England
    "old_trafford": {
        "name": "Old Trafford",
        "team": "Manchester United",
        "lat": 53.4631,
        "lon": -2.2913,
        "city": "Manchester",
        "country": "UK",
        "sport": "football",
        "capacity": 74879
    },
    "emirates": {
        "name": "Emirates Stadium",
        "team": "Arsenal",
        "lat": 51.5549,
        "lon": -0.1084,
        "city": "London",
        "country": "UK",
        "sport": "football",
        "capacity": 60704
    },
    "anfield": {
        "name": "Anfield",
        "team": "Liverpool",
        "lat": 53.4308,
        "lon": -2.9608,
        "city": "Liverpool",
        "country": "UK",
        "sport": "football",
        "capacity": 61015
    },
    "etihad": {
        "name": "Etihad Stadium",
        "team": "Manchester City",
        "lat": 53.4831,
        "lon": -2.2004,
        "city": "Manchester",
        "country": "UK",
        "sport": "football",
        "capacity": 55097
    },
    "stamford_bridge": {
        "name": "Stamford Bridge",
        "team": "Chelsea",
        "lat": 51.4817,
        "lon": -0.1910,
        "city": "London",
        "country": "UK",
        "sport": "football",
        "capacity": 40341
    },
    "tottenham_stadium": {
        "name": "Tottenham Hotspur Stadium",
        "team": "Tottenham Hotspur",
        "lat": 51.6042,
        "lon": -0.0662,
        "city": "London",
        "country": "UK",
        "sport": "football",
        "capacity": 62850
    },
    "st_james_park": {
        "name": "St James' Park",
        "team": "Newcastle United",
        "lat": 54.9756,
        "lon": -1.6217,
        "city": "Newcastle",
        "country": "UK",
        "sport": "football",
        "capacity": 52305
    },
    "villa_park": {
        "name": "Villa Park",
        "team": "Aston Villa",
        "lat": 52.5092,
        "lon": -1.8849,
        "city": "Birmingham",
        "country": "UK",
        "sport": "football",
        "capacity": 42640
    },
    
    # La Liga - Spain
    "camp_nou": {
        "name": "Camp Nou",
        "team": "Barcelona",
        "lat": 41.3809,
        "lon": 2.1228,
        "city": "Barcelona",
        "country": "Spain",
        "sport": "football",
        "capacity": 99354
    },
    "santiago_bernabeu": {
        "name": "Santiago Bernabéu",
        "team": "Real Madrid",
        "lat": 40.4530,
        "lon": -3.6883,
        "city": "Madrid",
        "country": "Spain",
        "sport": "football",
        "capacity": 81044
    },
    
    # Serie A - Italy
    "san_siro": {
        "name": "San Siro",
        "team": "AC Milan / Inter Milan",
        "lat": 45.4780,
        "lon": 9.1240,
        "city": "Milan",
        "country": "Italy",
        "sport": "football",
        "capacity": 75923
    },
    
    # Bundesliga - Germany
    "allianz_arena": {
        "name": "Allianz Arena",
        "team": "Bayern Munich",
        "lat": 48.2188,
        "lon": 11.6247,
        "city": "Munich",
        "country": "Germany",
        "sport": "football",
        "capacity": 75024
    },
    
    # Ligue 1 - France
    "parc_des_princes": {
        "name": "Parc des Princes",
        "team": "Paris Saint-Germain",
        "lat": 48.8414,
        "lon": 2.2530,
        "city": "Paris",
        "country": "France",
        "sport": "football",
        "capacity": 47929
    },
    
    # NFL - USA
    "sofi_stadium": {
        "name": "SoFi Stadium",
        "team": "LA Rams / LA Chargers",
        "lat": 33.9535,
        "lon": -118.3392,
        "city": "Los Angeles",
        "country": "USA",
        "sport": "american_football",
        "capacity": 70240
    },
    "metlife_stadium": {
        "name": "MetLife Stadium",
        "team": "NY Giants / NY Jets",
        "lat": 40.8128,
        "lon": -74.0742,
        "city": "New York",
        "country": "USA",
        "sport": "american_football",
        "capacity": 82500
    },
    
    # MLB - USA
    "yankee_stadium": {
        "name": "Yankee Stadium",
        "team": "New York Yankees",
        "lat": 40.8296,
        "lon": -73.9262,
        "city": "New York",
        "country": "USA",
        "sport": "baseball",
        "capacity": 46537
    },
    
    # NBA - USA
    "madison_square_garden": {
        "name": "Madison Square Garden",
        "team": "NY Knicks / NY Rangers",
        "lat": 40.7505,
        "lon": -73.9934,
        "city": "New York",
        "country": "USA",
        "sport": "basketball",
        "capacity": 20789
    },
}


def find_stadium(search_term):
    """
    Find stadium by name, team, or key
    
    Args:
        search_term: Stadium name, team name, or key (case-insensitive)
        
    Returns:
        Stadium dict or None if not found
    """
    search_term = search_term.lower().strip()
    
    # Direct key match
    if search_term in STADIUMS:
        return STADIUMS[search_term]
    
    # Search by name or team
    for key, stadium in STADIUMS.items():
        if (search_term in stadium['name'].lower() or 
            search_term in stadium['team'].lower() or
            search_term == key):
            return stadium
    
    return None


def list_stadiums(country=None, sport=None):
    """
    List all stadiums, optionally filtered
    
    Args:
        country: Filter by country (e.g., "UK", "USA")
        sport: Filter by sport (e.g., "football", "basketball")
        
    Returns:
        List of stadium dicts
    """
    results = []
    
    for key, stadium in STADIUMS.items():
        if country and stadium['country'] != country:
            continue
        if sport and stadium['sport'] != sport:
            continue
        results.append({**stadium, 'key': key})
    
    return results


def get_stadium_coords(search_term):
    """
    Get coordinates for a stadium
    
    Args:
        search_term: Stadium identifier
        
    Returns:
        (lat, lon) tuple or None
    """
    stadium = find_stadium(search_term)
    if stadium:
        return (stadium['lat'], stadium['lon'])
    return None
