"""
Raahi AI Safe Route Finder - Authenticated API Key Demonstration
================================================================
Demonstrates secure API Key authentication against the live Raahi server,
including client attribution, rate-limiting headers, quota telemetry, and
AI safety pathfinding.
"""

import sys
import json
import urllib.request
import urllib.error

API_BASE_URL = "http://127.0.0.1:8000"

# Registered Demo API Keys from seed.py
API_KEYS = {
    "growth": "raahi_key_growth_demo_2026_xyz456",      # MetroGuard Night Logistics (Growth Tier)
    "starter": "raahi_key_starter_demo_2026_xyz123",    # RapidDeliver Courier (Starter Tier)
    "city": "raahi_key_city_demo_2026_xyz000",          # Jaipur Municipal Smart City (B2G Tier)
    "invalid": "raahi_invalid_hacked_key_99999"         # Invalid Key for Security Testing
}

def make_request(method: str, endpoint: str, api_key: str = None, payload: dict = None):
    """Sends an HTTP request with optional X-API-Key header."""
    url = f"{API_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8")) if e.fp else {"error": str(e)}
        return e.code, body, dict(e.headers)
    except Exception as e:
        return 500, {"error": str(e)}, {}

def print_separator(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def main():
    print_separator("AUTHENTICATED AI ROUTE FINDER RUN (API KEY DEMO)")
    print(f"Target Server URL: {API_BASE_URL}")
    print(f"Selected Key     : {API_KEYS['growth']}")
    print(f"Client Profile   : MetroGuard Night Logistics (Growth Tier Plan)")

    # 1. Test Security: Reject Invalid API Key
    print_separator("STEP 1: SECURITY TEST (TAMPERED / INVALID API KEY)")
    code, resp, _ = make_request("POST", "/v1/route", api_key=API_KEYS["invalid"], payload={
        "origin": {"lat": 26.9180, "lon": 75.7950},
        "destination": {"lat": 26.8920, "lon": 75.8150}
    })
    print(f"Endpoint: POST /v1/route with invalid key")
    print(f"HTTP Status: {code} (Expected 401 Unauthorized)")
    print(f"Response: {resp}")
    assert code == 401, f"Security check failed! Status was {code}"
    print("  [PASSED] Unauthorized requests successfully blocked!")

    # 2. Test Quota & Usage Endpoint with Valid Key
    print_separator("STEP 2: CLIENT QUOTA & SUBSCRIPTION VERIFICATION")
    code, resp, headers = make_request("GET", "/v1/usage", api_key=API_KEYS["growth"])
    print(f"Endpoint: GET /v1/usage")
    print(f"HTTP Status: {code} OK")
    print(f"Client ID  : {resp.get('client_id')}")
    print(f"Plan Name  : {resp.get('plan_name')}")
    print(f"Quota Used : {resp.get('current_month_requests')} / {resp.get('monthly_quota')} requests")
    print(f"Rate Limit : {resp.get('rate_limit_per_minute')} requests / minute")

    # 3. Authenticated AI Segment Safety Prediction
    print_separator("STEP 3: AUTHENTICATED AI SEGMENT PREDICTION")
    pred_payload = {
        "street_lighting": 0.90,
        "pedestrian_activity": 0.80,
        "road_type": "primary",
        "incident_density": 0.0,
        "help_proximity": 0.85,
        "time_band": "late_night",
        "has_sidewalk": True,
        "weather_visibility": 1.0
    }
    code, resp, _ = make_request("POST", "/ai/predict_segment", api_key=API_KEYS["growth"], payload=pred_payload)
    print(f"Endpoint: POST /ai/predict_segment")
    print(f"HTTP Status: {code} OK")
    print(f"Client Telemetry: {resp.get('client_telemetry')}")
    print(f"AI Safety Score : {resp.get('safety_score_percentage')}%")
    print(f"Safety Tier     : {resp.get('safety_tier')}")
    print(f"Risk Multiplier : {resp.get('risk_penalty_multiplier')}x")
    print(f"Explanation     : {resp.get('explanation')}")

    # 4. Authenticated AI Night Routing Comparison
    print_separator("STEP 4: AUTHENTICATED AI NIGHT ROUTE OPTIMIZATION")
    route_payload = {
        "origin": {"lat": 26.9180, "lon": 75.7950},
        "destination": {"lat": 26.8920, "lon": 75.8150},
        "city_id": "jaipur",
        "time_band": "late_night"
    }
    code, resp, _ = make_request("POST", "/ai/route", api_key=API_KEYS["growth"], payload=route_payload)
    print(f"Endpoint: POST /ai/route (Sindhi Camp -> SMS Hospital)")
    print(f"HTTP Status: {code} OK")
    print(f"Client Telemetry: {resp.get('client_telemetry')}")
    
    short = resp.get("shortest_route", {})
    safe = resp.get("ai_safest_route", {})
    comp = resp.get("comparison", {})

    print("\nAUTHENTICATED ROUTE COMPARISON RESULTS:")
    print("-" * 70)
    print(f"{'Metric':<28} | {'Standard Shortest':<18} | {'Raahi AI Safest':<18}")
    print("-" * 70)
    print(f"{'Distance (m)':<28} | {short.get('total_distance_meters'):<18} | {safe.get('total_distance_meters'):<18}")
    print(f"{'Est. Walking Time (mins)':<28} | {short.get('estimated_walking_mins'):<18} | {safe.get('estimated_walking_mins'):<18}")
    print(f"{'AI Safety Score':<28} | {short.get('ai_composite_safety_score'):<18} | {safe.get('ai_composite_safety_score'):<18}")
    print(f"{'High Risk Exposure %':<28} | {str(short.get('red_risk_exposure_percentage')) + '%' :<18} | {str(safe.get('red_risk_exposure_percentage')) + '%' :<18}")
    print(f"{'Dark Stretch Avoided (m)':<28} | {'0.0 m':<18} | {str(comp.get('avoided_high_risk_meters')) + ' m':<18}")
    print("-" * 70)
    print(f"\nAI Natural Explanation:")
    print(f"  \"{comp.get('ai_explanation')}\"")
    print("=" * 70)
    print("Authenticated run completed successfully!\n")

if __name__ == "__main__":
    main()
