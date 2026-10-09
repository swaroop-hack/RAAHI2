"""
Raahi Pydantic Schemas for API Serialization and Validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LatLon(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)

class RouteWeights(BaseModel):
    lighting: Optional[float] = Field(None, ge=0.0, le=1.0)
    activity: Optional[float] = Field(None, ge=0.0, le=1.0)
    road_type: Optional[float] = Field(None, ge=0.0, le=1.0)
    incident_density: Optional[float] = Field(None, ge=0.0, le=1.0)
    help_proximity: Optional[float] = Field(None, ge=0.0, le=1.0)

class RouteRequest(BaseModel):
    origin: LatLon
    destination: LatLon
    city_id: Optional[str] = "jaipur"
    time_band: Optional[str] = "evening"  # evening, late_night, after_midnight
    profile: Optional[str] = "walking_alone"  # walking_alone, cycling, driving
    weights: Optional[RouteWeights] = None
    safety_slider: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    detour_cap: Optional[float] = Field(0.25, ge=0.05, le=1.5)

class RouteSegment(BaseModel):
    edge_id: str
    coordinates: List[List[float]]  # [[lat, lon], ...]
    length_m: float
    safety_score: float
    confidence: str  # 'high', 'medium', 'low'
    is_low_confidence: bool
    is_lit_imputed: bool
    road_type: str
    time_band: str

class RouteResult(BaseModel):
    label: str  # "Fastest" or "Raahi Safe Route"
    distance_m: float
    estimated_time_min: float
    average_safety_score: float
    worst_segment_score: float
    open_pois_passed: int
    unlit_low_activity_length_m: float
    confidence: str  # 'high', 'medium', 'low'
    has_simulated_data: bool
    has_live_data: bool
    has_low_confidence_stretches: bool
    coordinates: List[List[float]]  # [[lat, lon], ...]
    segments: List[RouteSegment]
    explanation: str

class RouteComparisonResponse(BaseModel):
    city_id: str
    time_band: str
    profile: str
    fastest_route: RouteResult
    safe_route: RouteResult
    detour_percentage: float
    safety_gain_percentage: float
    data_quality_summary: Dict[str, Any]
    disclaimer: str
    client_telemetry: Optional[Dict[str, Any]] = None

class ReportRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    report_type: str = Field(..., description="'dark'|'deserted'|'unsafe'|'other'")
    description: Optional[str] = None
    city_id: Optional[str] = "jaipur"

class ReportResponse(BaseModel):
    report_id: str
    snapped_edge_id: Optional[str]
    snap_distance_m: Optional[float]
    status: str
    corroboration_score: float
    is_corroborated: bool
    message: str

class SafeStopItem(BaseModel):
    poi_id: str
    poi_type: str
    name: Optional[str]
    lat: float
    lon: float
    distance_from_route_m: float
    is_open: bool

class VerificationReportResponse(BaseModel):
    city_id: str
    sample_size: int
    lighting_match_rate: float
    activity_match_rate: float
    overall_match_rate: float
    verified_edges_count: int
    total_edges_count: int
    coverage_percentage: float
    data_quality_label: str
    limitations_note: str

class BenchmarkResult(BaseModel):
    city_id: str
    sample_trips_count: int
    average_safety_gain_pct: float
    average_extra_distance_pct: float
    average_extra_time_min: float
    share_of_trips_meaningful_gain_pct: float
    data_source: str

class SensitivityResult(BaseModel):
    city_id: str
    perturbation_pct: float
    noise_level: float
    routes_unchanged_share_pct: float
    stability_label: str

class ValidationResult(BaseModel):
    city_id: str
    sample_ratings_count: int
    pearson_correlation: float
    spearman_correlation: float
    p_value: float
    summary: str

# B2B & monetization schemas
class ApiClientCreate(BaseModel):
    name: str
    plan_id: str
    city_id: str
    webhook_url: Optional[str] = None

class ApiClientResponse(BaseModel):
    client_id: str
    name: str
    plan_id: str
    city_id: str
    is_active: bool
    created_at: str
    raw_api_key: Optional[str] = None  # shown only once upon generation

class UsageSummaryResponse(BaseModel):
    client_id: str
    plan_id: str
    billing_period: str
    calls_today: int
    daily_limit: int
    calls_this_month: int
    monthly_quota: int
    remaining_quota: int
    estimated_bill_usd: float
    is_simulated: bool

class SegmentScoreItem(BaseModel):
    edge_id: str
    coordinates: List[List[float]]
    length_m: float
    road_type: str
    time_band: str
    composite_safety_score: float
    lighting_score: float
    activity_score: float
    road_type_score: float
    incident_density_score: float
    help_proximity_score: float
    confidence: str
    data_quality: str

class SegmentScoreResponse(BaseModel):
    city_id: str
    time_band: str
    count: int
    segments: List[SegmentScoreItem]

class WebhookPayload(BaseModel):
    event_type: str  # e.g., "corroborated_alert.created"
    city_id: str
    edge_id: str
    report_type: str
    corroboration_count: int
    timestamp: str
    signature: str

class FleetTripItem(BaseModel):
    trip_id: str
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float

class FleetEvaluationResponse(BaseModel):
    total_trips: int
    avg_safety_gain_pct: float
    avg_detour_pct: float
    trips: List[Dict[str, Any]]
