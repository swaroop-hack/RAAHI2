"""
Raahi AI Safe Route Finder - Model & Routing Demo
=================================================
Runs an end-to-end demonstration of the AI public safety evaluation model
and comparative night pathfinding engine.
"""

import sys
import os

# Ensure parent directory is on PYTHONPATH
cur_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(cur_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from raahi.ml.safety_model import get_ai_safety_model, SegmentFeatures
from raahi.ml.ai_router import get_ai_routes_for_trip

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def main():
    print_header("RAAHI: AI SAFE ROUTE FINDER FOR NIGHT TRAVEL")
    print("Initializing AI Model & verifying trained weights...")

    model = get_ai_safety_model()
    metrics = model.metrics

    print("\n[1] AI MODEL PERFORMANCE BENCHMARKS:")
    print("-" * 50)
    print(f"  * Regressor Architecture : Ensemble (HistGradientBoosting + RandomForest)")
    print(f"  * Classifier Architecture: RandomForestClassifier (3 Safety Tiers)")
    print(f"  * Regression R^2 Score   : {metrics.get('r2_score', 'N/A')}")
    print(f"  * Mean Absolute Error    : {metrics.get('mean_absolute_error', 'N/A')}")
    print(f"  * Root Mean Squared Error: {metrics.get('root_mean_squared_error', 'N/A')}")
    print(f"  * Safety Tier Accuracy   : {metrics.get('classification_accuracy', 0.0) * 100:.1f}%")
    print(f"  * Training / Test Samples: {metrics.get('train_samples', 0)} / {metrics.get('test_samples', 0)}")

    print("\n[2] TOP PUBLIC-SAFETY FEATURE CONTRIBUTIONS:")
    print("-" * 50)
    for feat, imp in sorted(model.feature_importances_.items(), key=lambda x: x[1], reverse=True)[:6]:
        bar = "#" * int(imp * 40)
        print(f"  {feat:22} : {imp:6.3f} | {bar}")

    print_header("EVALUATION ON DIVERSE NIGHT SEGMENT SCENARIOS")
    scenarios = [
        ("Well-Lit Commercial Boulevard", SegmentFeatures(
            street_lighting=0.95, pedestrian_activity=0.85, road_type="primary",
            incident_density=0.0, help_proximity=0.90, time_band="evening", has_sidewalk=True
        )),
        ("Quiet Suburban Residential Lane", SegmentFeatures(
            street_lighting=0.55, pedestrian_activity=0.30, road_type="residential",
            incident_density=0.05, help_proximity=0.45, time_band="late_night", has_sidewalk=True
        )),
        ("Transit Hub / Night Market", SegmentFeatures(
            street_lighting=0.85, pedestrian_activity=0.90, road_type="secondary",
            incident_density=0.20, help_proximity=0.75, time_band="late_night", has_sidewalk=True
        )),
        ("Dark Deserted Alley Shortcut", SegmentFeatures(
            street_lighting=0.05, pedestrian_activity=0.05, road_type="alley",
            incident_density=0.75, help_proximity=0.05, time_band="after_midnight", has_sidewalk=False
        )),
    ]

    for name, feat in scenarios:
        res = model.predict_segment(feat)
        print(f"\nScenario: {name}")
        print(f"  Lighting: {feat.street_lighting*100:.0f}% | Foot Traffic: {feat.pedestrian_activity*100:.0f}% | Incidents: {feat.incident_density*100:.0f}%")
        print(f"  AI Safety Score: {res.safety_score*100:.1f} / 100 | Tier: {res.safety_tier}")
        print(f"  Routing Cost Penalty Multiplier: {res.risk_multiplier:.2f}x")
        print(f"  Explanation: {res.explanation}")

    print_header("REAL TRIP EVALUATION & ROUTE COMPARISON (JAIPUR AT NIGHT)")
    # Origin: Sindhi Camp Bus Terminal -> Destination: SMS Hospital
    orig_lat, orig_lon = 26.9180, 75.7950
    dest_lat, dest_lon = 26.8920, 75.8150

    print(f"Trip Origin     : ({orig_lat}, {orig_lon}) [Sindhi Camp]")
    print(f"Trip Destination: ({dest_lat}, {dest_lon}) [SMS Hospital Area]")
    print(f"Departure Time  : Late Night (22:30)")

    trip_res = get_ai_routes_for_trip(orig_lat, orig_lon, dest_lat, dest_lon, city_id="jaipur", time_band="late_night")
    short = trip_res["shortest_route"]
    safe = trip_res["ai_safest_route"]
    comp = trip_res["comparison"]

    print("\nCOMPARISON TABLE:")
    print("-" * 70)
    print(f"{'Metric':<28} | {'Standard Shortest':<18} | {'Raahi AI Safest':<18}")
    print("-" * 70)
    print(f"{'Total Distance (m)':<28} | {short['total_distance_meters']:<18.1f} | {safe['total_distance_meters']:<18.1f}")
    print(f"{'Walking Time (mins)':<28} | {short['estimated_walking_mins']:<18.1f} | {safe['estimated_walking_mins']:<18.1f}")
    print(f"{'AI Night Safety Score':<28} | {short['ai_composite_safety_score']:<18.1f} | {safe['ai_composite_safety_score']:<18.1f}")
    print(f"{'High-Risk Exposure %':<28} | {short['red_risk_exposure_percentage']:<17.1f}% | {safe['red_risk_exposure_percentage']:<17.1f}%")
    print(f"{'High-Risk Distance (m)':<28} | {short['red_risk_distance_meters']:<18.1f} | {safe['red_risk_distance_meters']:<18.1f}")
    print("-" * 70)

    print("\nAI COMPARATIVE INSIGHT:")
    print(f"  * Detour Penalty      : +{comp['detour_percentage']}% ({safe['total_distance_meters'] - short['total_distance_meters']:.0f}m extra)")
    print(f"  * Safety Improvement  : +{comp['safety_gain_percentage']}%")
    print(f"  * Dark Stretch Avoided: {comp['avoided_high_risk_meters']:.1f} meters")
    print(f"  * AI Explanation      : {comp['ai_explanation']}")
    print("=" * 70)
    print("Demo completed successfully!\n")

if __name__ == "__main__":
    main()
