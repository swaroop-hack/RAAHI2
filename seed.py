"""
Raahi Seed Script
Populates demo clients across all subscription tiers, generates hashed API keys,
seeds sample usage events, and sets up city dashboard content.
"""

import os
import sys
import types
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

# Ensure root directory is on sys.path and aliased as 'raahi' package for cloud deploys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if "raahi" not in sys.modules:
    raahi_pkg = types.ModuleType("raahi")
    raahi_pkg.__path__ = [BASE_DIR]
    sys.modules["raahi"] = raahi_pkg

from raahi.database import SessionLocal, Base, engine
from raahi.models import Plan, ApiClient, ApiKey, UsageEvent, UserReport, City
from raahi.config import settings
from raahi.ingestion.ingest_osm import ingest_city_osm
from raahi.core.features import compute_and_store_features_for_city
from raahi.core.verify import run_cross_source_checks, ingest_sample_field_checks

DEMO_KEYS = {
    "api_starter": "raahi_key_starter_demo_2026_xyz123",
    "api_growth": "raahi_key_growth_demo_2026_xyz456",
    "fleet": "raahi_key_fleet_demo_2026_xyz789",
    "city": "raahi_key_city_demo_2026_xyz000",
    "whitelabel": "raahi_key_whitelabel_demo_2026_xyz999"
}

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    print("1. Seeding Base Plans...")
    for p_id, p_info in settings.PLANS.items():
        existing = db.query(Plan).filter(Plan.plan_id == p_id).first()
        if not existing:
            plan_obj = Plan(
                plan_id=p_id,
                name=p_info["name"],
                price_monthly_usd=p_info["price_monthly_usd"],
                price_per_vehicle_usd=p_info.get("price_per_vehicle_usd", 0.0),
                daily_routes_limit=p_info["daily_routes_limit"],
                monthly_quota=p_info["monthly_quota"],
                rate_limit_per_minute=p_info["rate_limit_per_minute"],
                allows_api=p_info["allows_api"],
                allows_segment_scores=p_info["allows_segment_scores"],
                allows_webhooks=p_info["allows_webhooks"],
                allows_fleet=p_info["allows_fleet"],
                allows_city_dashboard=p_info["allows_city_dashboard"],
                source="seed_script",
                data_quality="real"
            )
            db.add(plan_obj)
    db.commit()

    print("2. Ensuring City & Network Topology...")
    ingest_city_osm("jaipur", force_reload=False)
    compute_and_store_features_for_city("jaipur")
    run_cross_source_checks("jaipur")
    ingest_sample_field_checks("jaipur")

    print("3. Seeding Demo B2B/B2G Clients...")
    demo_clients_def = [
        ("cli_demo_starter", "RapidDeliver Courier", "api_starter", "jaipur", DEMO_KEYS["api_starter"]),
        ("cli_demo_growth", "MetroGuard Night Logistics", "api_growth", "jaipur", DEMO_KEYS["api_growth"]),
        ("cli_demo_fleet", "PinkCity Cabs & Fleet", "fleet", "jaipur", DEMO_KEYS["fleet"]),
        ("cli_demo_city", "Jaipur Smart City Municipal Corp (B2G)", "city", "jaipur", DEMO_KEYS["city"]),
        ("cli_demo_whitelabel", "Global Shield Mobility", "whitelabel", "jaipur", DEMO_KEYS["whitelabel"]),
    ]

    for c_id, name, p_id, city, raw_key in demo_clients_def:
        existing_client = db.query(ApiClient).filter(ApiClient.client_id == c_id).first()
        if not existing_client:
            client_obj = ApiClient(
                client_id=c_id,
                name=name,
                plan_id=p_id,
                city_id=city,
                webhook_url="https://webhook.site/demo-raahi-receiver",
                webhook_secret="demo_secret_key_12345",
                is_active=True,
                source="seed_script",
                data_quality="real"
            )
            db.add(client_obj)

        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        existing_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if not existing_key:
            key_obj = ApiKey(
                key_id=f"key_{c_id}",
                client_id=c_id,
                key_hash=key_hash,
                key_prefix=raw_key[:12],
                is_revoked=False,
                source="seed_script",
                data_quality="real"
            )
            db.add(key_obj)
    db.commit()

    print("4. Seeding Usage Events for Analytics & Metering...")
    # Add usage events across past few days
    now = datetime.now(timezone.utc)
    sample_events = []
    
    # Growth client usage: 450 calls
    for day_offset in range(5):
        ts = now - timedelta(days=day_offset, hours=2)
        for _ in range(80):
            sample_events.append(UsageEvent(
                client_id="cli_demo_growth",
                endpoint="/v1/route",
                method="POST",
                city_id="jaipur",
                billable_units=1,
                response_status=200,
                timestamp=ts,
                source="seed_usage",
                data_quality="real"
            ))

    # Starter client usage: 120 calls
    for _ in range(120):
        sample_events.append(UsageEvent(
            client_id="cli_demo_starter",
            endpoint="/v1/route",
            method="POST",
            city_id="jaipur",
            billable_units=1,
            response_status=200,
            timestamp=now - timedelta(hours=3),
            source="seed_usage",
            data_quality="real"
        ))

    db.bulk_save_objects(sample_events)
    db.commit()

    print("5. Seeding Sample Corroborated Reports for City Dashboard...")
    # Add a cluster of dark / deserted reports on jaipur_122_111_0 (service alley)
    alley_reports = [
        ("rep_seed_1", "jaipur_122_111_0", "dark", "Unlit dark stretch near boundary wall", 26.9110, 75.8010, True, 3.0),
        ("rep_seed_2", "jaipur_122_111_0", "dark", "Broken street lamp, zero footfall", 26.9112, 75.8012, True, 3.0),
        ("rep_seed_3", "jaipur_122_111_0", "deserted", "Completely empty after 10 PM", 26.9115, 75.8014, True, 3.0),
        ("rep_seed_4", "jaipur_124_105_0", "dark", "Narrow lane with no lighting", 26.9270, 75.8210, True, 2.0),
        ("rep_seed_5", "jaipur_120_121_0", "deserted", "Quiet residential boundary", 26.9360, 75.7850, False, 1.0)
    ]
    for r_id, edge_id, r_type, desc, lat, lon, corrob, c_score in alley_reports:
        if not db.query(UserReport).filter(UserReport.report_id == r_id).first():
            db.add(UserReport(
                report_id=r_id,
                city_id="jaipur",
                edge_id=edge_id,
                report_type=r_type,
                description=desc,
                lat=lat,
                lon=lon,
                snap_distance_m=12.0,
                is_anonymous=True,
                client_ip_hash="seed_hash_demo",
                corroboration_score=c_score,
                is_corroborated=corrob,
                source="seed_data",
                data_quality="real",
                timestamp=now - timedelta(days=2)
            ))
    db.commit()

    print("\n[OK] Seed completed successfully!")
    print("Demo API Keys:")
    for plan_id, k in DEMO_KEYS.items():
        print(f"  [{plan_id:12}] Key: {k}")

    db.close()

if __name__ == "__main__":
    seed_database()
