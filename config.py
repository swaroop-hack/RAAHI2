"""
Raahi Configuration Module
Centralized, single source of truth for:
- Database settings (SQLite / SpatiaLite / PostGIS)
- City boundaries, default coordinates, and spatial buffers
- Time-of-day bands and POI operating hour profiles
- Profile weights and safety calculation parameters
- Monetization plans, quotas, and simulated pricing
"""

from pydantic import BaseModel
from typing import Dict, Any, List

class CityConfig(BaseModel):
    city_id: str
    name: str
    country: str
    bbox: tuple[float, float, float, float]  # min_lat, min_lon, max_lat, max_lon
    center: tuple[float, float]  # lat, lon
    search_radius_m: float = 4000.0

class Settings:
    PROJECT_NAME: str = "Raahi"
    VERSION: str = "1.0.0"
    DEFAULT_CITY_ID: str = "jaipur"
    
    # Database: SQLite default, swappable to PostgreSQL/PostGIS via DATABASE_URL
    DATABASE_URL: str = "sqlite:///./raahi.db"
    
    # Supported Cities Registry
    CITIES: Dict[str, CityConfig] = {
        "jaipur": CityConfig(
            city_id="jaipur",
            name="Jaipur",
            country="India",
            bbox=(26.8500, 75.7500, 26.9600, 75.8700),
            center=(26.9124, 75.7873),
            search_radius_m=4500.0
        ),
        "delhi": CityConfig(
            city_id="delhi",
            name="Delhi",
            country="India",
            bbox=(28.5500, 77.1000, 28.7000, 77.3000),
            center=(28.6139, 77.2090),
            search_radius_m=5000.0
        )
    }
    
    # Spatial analysis parameters
    POI_BUFFER_METERS: float = 120.0
    HELP_SEARCH_RADIUS_METERS: float = 1500.0
    MAX_SNAP_DISTANCE_METERS: float = 150.0
    
    # Time Bands definitions
    # evening: 18:00 - 21:00 (6-9 PM)
    # late_night: 21:00 - 00:00 (9 PM - 12 AM)
    # after_midnight: 00:00 - 05:00 (12 AM - 5 AM)
    TIME_BANDS: List[str] = ["evening", "late_night", "after_midnight"]
    
    # POI Openness Probabilities / Status per Time Band
    POI_OPEN_PROBABILITIES: Dict[str, Dict[str, float]] = {
        "atm": {"evening": 1.0, "late_night": 0.95, "after_midnight": 0.90},
        "fuel": {"evening": 1.0, "late_night": 0.90, "after_midnight": 0.80},
        "hospital": {"evening": 1.0, "late_night": 1.0, "after_midnight": 1.0},
        "police": {"evening": 1.0, "late_night": 1.0, "after_midnight": 1.0},
        "pharmacy": {"evening": 1.0, "late_night": 0.85, "after_midnight": 0.50},
        "convenience": {"evening": 1.0, "late_night": 0.70, "after_midnight": 0.30},
        "restaurant": {"evening": 1.0, "late_night": 0.60, "after_midnight": 0.10},
        "cafe": {"evening": 0.95, "late_night": 0.40, "after_midnight": 0.05},
        "shop": {"evening": 0.90, "late_night": 0.20, "after_midnight": 0.01},
        "bank": {"evening": 0.30, "late_night": 0.0, "after_midnight": 0.0},
        "default": {"evening": 0.80, "late_night": 0.30, "after_midnight": 0.05}
    }
    
    # Road Type base safety and lighting baseline priors
    ROAD_TYPE_SCORES: Dict[str, float] = {
        "primary": 0.85,
        "primary_link": 0.80,
        "secondary": 0.80,
        "secondary_link": 0.75,
        "tertiary": 0.70,
        "tertiary_link": 0.65,
        "residential": 0.55,
        "living_street": 0.50,
        "pedestrian": 0.65,
        "footway": 0.40,
        "path": 0.35,
        "service": 0.30,
        "unclassified": 0.45,
        "track": 0.25,
        "alley": 0.20,
        "default": 0.50
    }
    
    # Default feature weights by commuter profile
    PROFILE_WEIGHTS: Dict[str, Dict[str, float]] = {
        "walking_alone": {
            "lighting": 0.35,
            "activity": 0.25,
            "road_type": 0.15,
            "incident_density": 0.15,
            "help_proximity": 0.10
        },
        "cycling": {
            "lighting": 0.30,
            "activity": 0.20,
            "road_type": 0.25,
            "incident_density": 0.15,
            "help_proximity": 0.10
        },
        "driving": {
            "lighting": 0.25,
            "activity": 0.15,
            "road_type": 0.35,
            "incident_density": 0.15,
            "help_proximity": 0.10
        }
    }
    
    # Routing constraints
    DEFAULT_DETOUR_CAP: float = 0.25  # 25% max extra distance over fastest
    DEFAULT_SAFETY_SLIDER: float = 0.5  # 0.0 = pure speed, 1.0 = maximum safety
    WORST_SEGMENT_PENALTY_WEIGHT: float = 0.35  # penalty factor for lowest-scoring stretch
    MIN_SAFETY_THRESHOLD: float = 0.30  # threshold below which edge costs are heavily penalized
    
    # Feedback & Reporting
    REPORT_HALF_LIFE_DAYS: float = 14.0  # exponential time decay
    CORROBORATION_COUNT: int = 3         # reports needed on edge for high impact
    BURST_RATE_LIMIT_PER_MINUTE: int = 10
    
    # Monetization & B2B Plans
    PLANS: Dict[str, Dict[str, Any]] = {
        "free": {
            "name": "Free Consumer",
            "price_monthly_usd": 0.0,
            "daily_routes_limit": 25,
            "monthly_quota": 750,
            "rate_limit_per_minute": 30,
            "allows_api": False,
            "allows_segment_scores": False,
            "allows_webhooks": False,
            "allows_fleet": False,
            "allows_city_dashboard": False
        },
        "api_starter": {
            "name": "API Starter",
            "price_monthly_usd": 49.0,
            "daily_routes_limit": 1000,
            "monthly_quota": 25000,
            "rate_limit_per_minute": 120,
            "allows_api": True,
            "allows_segment_scores": False,
            "allows_webhooks": False,
            "allows_fleet": False,
            "allows_city_dashboard": False
        },
        "api_growth": {
            "name": "API Growth",
            "price_monthly_usd": 199.0,
            "daily_routes_limit": 10000,
            "monthly_quota": 250000,
            "rate_limit_per_minute": 600,
            "allows_api": True,
            "allows_segment_scores": True,
            "allows_webhooks": True,
            "allows_fleet": False,
            "allows_city_dashboard": False
        },
        "fleet": {
            "name": "Fleet Mobility",
            "price_monthly_usd": 499.0,
            "price_per_vehicle_usd": 5.0,
            "daily_routes_limit": 50000,
            "monthly_quota": 1000000,
            "rate_limit_per_minute": 1200,
            "allows_api": True,
            "allows_segment_scores": True,
            "allows_webhooks": True,
            "allows_fleet": True,
            "allows_city_dashboard": False
        },
        "city": {
            "name": "City Municipal & B2G",
            "price_monthly_usd": 1499.0,
            "daily_routes_limit": 100000,
            "monthly_quota": 2500000,
            "rate_limit_per_minute": 2400,
            "allows_api": True,
            "allows_segment_scores": True,
            "allows_webhooks": True,
            "allows_fleet": True,
            "allows_city_dashboard": True
        },
        "whitelabel": {
            "name": "Enterprise White-label",
            "price_monthly_usd": 3999.0,
            "daily_routes_limit": 500000,
            "monthly_quota": 10000000,
            "rate_limit_per_minute": 6000,
            "allows_api": True,
            "allows_segment_scores": True,
            "allows_webhooks": True,
            "allows_fleet": True,
            "allows_city_dashboard": True,
            "allows_custom_branding": True
        }
    }

settings = Settings()
