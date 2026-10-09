"""
Raahi SQLAlchemy ORM Models
Defines tables for core spatial data, user reports, surveys, verification,
API clients, keys, usage, plans, and simulated invoices.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from raahi.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class City(Base):
    __tablename__ = "cities"
    
    city_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="India")
    min_lat = Column(Float, nullable=False)
    min_lon = Column(Float, nullable=False)
    max_lat = Column(Float, nullable=False)
    max_lon = Column(Float, nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    
    # Audit columns
    source = Column(String(50), default="osm")
    data_quality = Column(String(50), default="real")  # 'real'|'proxy'|'survey'|'live'|'verified'|'simulated'
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    
    # Relationships
    edges = relationship("Edge", back_populates="city", cascade="all, delete-orphan")
    pois = relationship("POI", back_populates="city", cascade="all, delete-orphan")

class Edge(Base):
    __tablename__ = "edges"
    
    edge_id = Column(String(100), primary_key=True, index=True)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False, index=True)
    u = Column(Integer, nullable=False)
    v = Column(Integer, nullable=False)
    key = Column(Integer, default=0)
    
    geometry_wkt = Column(Text, nullable=False)  # LINESTRING WKT
    length = Column(Float, nullable=False)  # in meters
    road_type = Column(String(50), default="residential")
    lit_tag = Column(String(20), nullable=True)  # 'yes', 'no', etc.
    sidewalk_tag = Column(String(50), nullable=True)
    maxspeed = Column(String(20), nullable=True)
    
    # Audit & verification
    source = Column(String(50), default="osm")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    last_verified = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    city = relationship("City", back_populates="edges")
    features = relationship("EdgeFeature", back_populates="edge", cascade="all, delete-orphan")
    reports = relationship("UserReport", back_populates="edge")

    __table_args__ = (
        Index("idx_edges_city_uv", "city_id", "u", "v"),
    )

class POI(Base):
    __tablename__ = "pois"
    
    poi_id = Column(String(100), primary_key=True, index=True)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False, index=True)
    poi_type = Column(String(50), nullable=False)  # hospital, police, pharmacy, atm, shop
    name = Column(String(150), nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    opening_hours = Column(String(100), nullable=True)
    is_24x7 = Column(Boolean, default=False)
    
    source = Column(String(50), default="osm")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    
    city = relationship("City", back_populates="pois")

    __table_args__ = (
        Index("idx_pois_city_type", "city_id", "poi_type"),
    )

class EdgeFeature(Base):
    __tablename__ = "edge_features"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    edge_id = Column(String(100), ForeignKey("edges.edge_id"), nullable=False, index=True)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False, index=True)
    time_band = Column(String(30), nullable=False, index=True)  # evening, late_night, after_midnight
    
    # Normalized feature scores (0-1 percentile across city)
    lighting_score = Column(Float, nullable=False, default=0.5)
    is_lit_imputed = Column(Boolean, default=True)
    activity_score = Column(Float, nullable=False, default=0.5)
    road_type_score = Column(Float, nullable=False, default=0.5)
    incident_density_score = Column(Float, nullable=False, default=0.5)
    help_proximity_score = Column(Float, nullable=False, default=0.5)
    composite_safety_score = Column(Float, nullable=False, default=0.5)
    
    confidence = Column(String(20), default="medium")  # 'high', 'medium', 'low'
    real_feature_count = Column(Integer, default=1)
    imputed_feature_count = Column(Integer, default=1)
    agreement_count = Column(Integer, default=0)
    disagreement_count = Column(Integer, default=0)
    
    source = Column(String(50), default="computed")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    
    edge = relationship("Edge", back_populates="features")

    __table_args__ = (
        Index("idx_edge_features_lookup", "city_id", "edge_id", "time_band", unique=True),
    )

class UserReport(Base):
    __tablename__ = "user_reports"
    
    report_id = Column(String(100), primary_key=True, index=True)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False, index=True)
    edge_id = Column(String(100), ForeignKey("edges.edge_id"), nullable=True, index=True)
    report_type = Column(String(50), nullable=False)  # dark, deserted, unsafe, other
    description = Column(Text, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    snap_distance_m = Column(Float, nullable=True)
    is_anonymous = Column(Boolean, default=True)
    client_ip_hash = Column(String(64), nullable=True)
    
    corroboration_score = Column(Float, default=1.0)
    is_corroborated = Column(Boolean, default=False)
    
    source = Column(String(50), default="consumer_app")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    
    edge = relationship("Edge", back_populates="reports")

class SurveyWeight(Base):
    __tablename__ = "survey_weights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False, index=True)
    lighting_rank = Column(Float, nullable=False)
    activity_rank = Column(Float, nullable=False)
    road_type_rank = Column(Float, nullable=False)
    incidents_rank = Column(Float, nullable=False)
    help_proximity_rank = Column(Float, nullable=False)
    respondent_category = Column(String(50), default="resident")
    
    source = Column(String(50), default="survey_csv")
    data_quality = Column(String(50), default="survey")
    timestamp = Column(DateTime(timezone=True), default=utcnow)

class SurveyRating(Base):
    __tablename__ = "survey_ratings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False, index=True)
    route_or_area = Column(String(100), nullable=False)
    rating_score = Column(Float, nullable=False)  # 1 to 5
    
    source = Column(String(50), default="survey_csv")
    data_quality = Column(String(50), default="survey")
    timestamp = Column(DateTime(timezone=True), default=utcnow)

class FieldCheck(Base):
    __tablename__ = "field_checks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False, index=True)
    edge_id = Column(String(100), ForeignKey("edges.edge_id"), nullable=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    observed_lighting = Column(Float, nullable=False)  # 0 to 1
    observed_activity = Column(Float, nullable=False)  # 0 to 1
    check_date = Column(DateTime(timezone=True), default=utcnow)
    method = Column(String(50), default="walk_audit")
    
    source = Column(String(50), default="field_audit")
    data_quality = Column(String(50), default="verified")
    timestamp = Column(DateTime(timezone=True), default=utcnow)

class Plan(Base):
    __tablename__ = "plans"
    
    plan_id = Column(String(50), primary_key=True)  # free, api_starter, api_growth, fleet, city, whitelabel
    name = Column(String(100), nullable=False)
    price_monthly_usd = Column(Float, default=0.0)
    price_per_vehicle_usd = Column(Float, default=0.0)
    daily_routes_limit = Column(Integer, default=25)
    monthly_quota = Column(Integer, default=750)
    rate_limit_per_minute = Column(Integer, default=30)
    allows_api = Column(Boolean, default=False)
    allows_segment_scores = Column(Boolean, default=False)
    allows_webhooks = Column(Boolean, default=False)
    allows_fleet = Column(Boolean, default=False)
    allows_city_dashboard = Column(Boolean, default=False)
    
    source = Column(String(50), default="system")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)

class ApiClient(Base):
    __tablename__ = "api_clients"
    
    client_id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    plan_id = Column(String(50), ForeignKey("plans.plan_id"), nullable=False)
    city_id = Column(String(50), ForeignKey("cities.city_id"), nullable=False)
    webhook_url = Column(String(255), nullable=True)
    webhook_secret = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    
    source = Column(String(50), default="admin")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    
    keys = relationship("ApiKey", back_populates="client", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="client")

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    key_id = Column(String(50), primary_key=True)
    client_id = Column(String(50), ForeignKey("api_clients.client_id"), nullable=False)
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    source = Column(String(50), default="system")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    
    client = relationship("ApiClient", back_populates="keys")

class UsageEvent(Base):
    __tablename__ = "usage_events"
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(50), ForeignKey("api_clients.client_id"), nullable=False, index=True)
    endpoint = Column(String(100), nullable=False)
    method = Column(String(10), default="POST")
    city_id = Column(String(50), nullable=False)
    billable_units = Column(Integer, default=1)
    response_status = Column(Integer, default=200)
    
    source = Column(String(50), default="metering")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    
    client = relationship("ApiClient", back_populates="usage_events")

class InvoiceSimulated(Base):
    __tablename__ = "invoices_simulated"
    
    invoice_id = Column(String(100), primary_key=True)
    client_id = Column(String(50), ForeignKey("api_clients.client_id"), nullable=False, index=True)
    billing_period = Column(String(20), nullable=False)  # 'YYYY-MM'
    plan_id = Column(String(50), nullable=False)
    base_fee_usd = Column(Float, default=0.0)
    metered_calls = Column(Integer, default=0)
    overage_fee_usd = Column(Float, default=0.0)
    total_amount_usd = Column(Float, default=0.0)
    status = Column(String(30), default="simulated_paid")
    is_simulated = Column(Boolean, default=True)
    
    source = Column(String(50), default="billing_engine")
    data_quality = Column(String(50), default="simulated")
    timestamp = Column(DateTime(timezone=True), default=utcnow)

class SystemConfig(Base):
    __tablename__ = "config"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    
    source = Column(String(50), default="system")
    data_quality = Column(String(50), default="real")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
