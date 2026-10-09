# Raahi: Safe Route Finder for Night Travel - Implementation Plan

## 1. Project Overview & Architecture
Raahi is an autonomous, data-driven navigation platform designed for night-time commuters (women traveling alone, night-shift workers, delivery riders, students, and visitors). Instead of optimizing solely for distance or travel time, Raahi identifies, evaluates, and compares routes across multiple public-safety parameters:
- Street lighting (`lit` tag + road type / POI density imputation + cross-source satellite/reports verification)
- Pedestrian and commercial activity (open POIs within buffer per time band, e.g. 24x7 ATMs/pharmacies vs closed daytime retail)
- Road classification & infrastructure (primary/secondary with sidewalks vs service/alley/unlit footpaths)
- Incident density (historical & reported safety flags with exponential time decay)
- Proximity to help (police stations, hospitals, 24x7 verified stores)

Raahi operates dual business tiers:
1. **Free Consumer App**: Web-based map interface for finding fastest vs safest routes, explaining trade-offs ("12% longer but passes 6 open shops and 2 well-lit roads"), viewing data quality badges, and submitting anonymous reports ("Tell Raahi").
2. **B2B & B2G Platform**: Authenticated API keys, rate limits, monthly quotas, segment scores endpoint (`/v1/segment_scores`), signed webhook alerts (`/v1/webhooks`), city municipal dashboard (ranked repair priorities, heatmap, CSV export), fleet routing analytics (batch CSV trip evaluator), admin platform analytics, and simulated billing invoice generator.

---

## 2. Directory Structure

```
raahi/
├── config.py                     # Unified configuration (city, weights, time bands, plans, prices, limits)
├── database.py                   # SQLAlchemy engine, session maker, SpatiaLite/SQLite & PostGIS support
├── models.py                     # ORM Models (cities, edges, pois, edge_features, user_reports, etc.)
├── schemas.py                    # Pydantic schemas for API inputs and outputs
├── PLAN.md                       # Architecture, folder structure, assumptions, phase roadmap
├── PROGRESS.md                   # Real-time build logs per phase, failures, fixes, verification proofs
├── requirements.txt              # Production and development dependencies
├── Dockerfile                    # Containerization for standalone deployment
├── docker-compose.yml            # Compose setup for app + DB
│
├── ingestion/
│   ├── __init__.py
│   ├── ingest_osm.py             # OSM graph and POIs downloader & parser (with offline mock fallback if needed)
│   ├── ingest_enrichment.py      # Importer for raw CSV/GeoTIFF raster, population, streetlights, incidents
│   ├── ingest_survey.py          # Weight preference survey & route rating ground truth survey importer
│   └── generate_sample_data.py   # Test incident/lighting generator (marked data_quality = 'simulated')
│
├── core/
│   ├── __init__.py
│   ├── features.py               # Edge feature calculation, imputation (default 0.5), length-weighting, percentiles
│   ├── routing.py                # Graph construction, cost lambda slider, Dijkstra/A*, detour cap, worst penalty
│   ├── feedback.py               # User report snapping, decay, corroboration thresholds, duplicate merging
│   └── verify.py                 # Cross-source agreement checks, confidence labeling, field verification importer
│
├── live/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py               # Pluggable adapter interface (fetch, normalise, health_check)
│   │   ├── weather.py            # Open-Meteo live visibility/weather adapter with graceful fallback
│   │   ├── reports.py            # Live user report decay adapter
│   │   └── stubs.py              # Traffic, municipal outages, partner fleet stub adapters (disabled by default)
│   └── manager.py                # Live data coordinator with fail-safe caching and TTL
│
├── api/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application factory and mounting
│   ├── middleware.py             # API Key authentication, rate-limiting, usage logging
│   ├── routes_consumer.py        # /route, /explain, /report, /safe_stops, /health, /benchmark, /sensitivity, etc.
│   ├── routes_b2b.py             # /v1/route, /v1/segment_scores, /v1/webhooks, /usage
│   └── routes_admin.py           # Admin client management, keys, fleet upload, city dashboard stats
│
├── billing/
│   ├── __init__.py
│   └── generate_invoices.py      # Monthly simulated invoice calculation and record generation
│
├── cli/
│   ├── __init__.py
│   └── add_city.py               # CLI tool `python -m raahi.add_city "<City, Country>"`
│
├── static/                       # Frontend web assets
│   ├── index.html                # Consumer SPA with Leaflet map, sliders, comparison, reporting modal
│   ├── city_dashboard.html       # Municipal City Dashboard (ranked segments, heatmap, export)
│   ├── fleet_dashboard.html      # Fleet O/D CSV Trip evaluation and batch comparison view
│   ├── admin_dashboard.html      # Platform usage analytics and client management
│   ├── css/
│   │   └── style.css             # High-contrast, clean theme (dark/night-safe aesthetic)
│   └── js/
│       ├── app.js                # Consumer map interaction, routing queries, slider updates
│       ├── city.js               # City dashboard rendering, segment ranking, CSV export
│       ├── fleet.js              # Fleet batch upload and statistics
│       └── admin.js              # Admin usage charts and client management
│
├── tests/
│   ├── test_features.py          # Imputation, percentiles, confidence labeling tests
│   ├── test_routing.py           # Dijkstra, detour cap, worst-segment penalty, weights
│   ├── test_feedback.py          # Snapping, decay, corroboration threshold, duplicate merging
│   ├── test_verify.py            # Verification checks, field checks match rate
│   ├── test_live.py              # Open-Meteo fail-safe fallback, live badges
│   ├── test_api_security.py      # API keys, hashing, rate limits, quota enforcement
│   └── test_billing.py           # Simulated invoice computation and usage math
│
├── data/
│   ├── raw/                      # Raw enrichment files, survey inputs, field verification CSVs
│   └── sample/                   # Seed files for quick demo and zero-configuration run
│
└── seed.py                       # Demo client seeder (free, api_starter, api_growth, fleet, city, whitelabel)
```

---

## 3. Assumptions & Architectural Decisions
1. **City Agnostic**: Default city is `Jaipur, India`. All DB queries and graph components are keyed by `city_id`.
2. **Missing Feature Imputation**: Missing values strictly default to `0.5`, never `0.0`. Imputed flags are preserved.
3. **Data Quality Tracking**: Every record explicitly carries `data_quality` in `('real', 'proxy', 'survey', 'live', 'verified', 'simulated')`.
4. **Resilient Graph Ingestion**: OSMnx queries the OpenStreetMap Overpass API for real street networks and POIs. If external network connectivity is restricted or throttled during ingestion, an offline geometric fallback graph for Jaipur is generated with identical schema and realistic topology to ensure 100% testability and reliability.
5. **Neutral Safety Terminology**: Labels use "less lit", "low activity at night", "moderate footfall". Words like "dangerous" or "high-crime area" are never used.
6. **Simulated Billing**: Invoices are strictly calculated and tagged with `data_quality = 'simulated'` and `is_simulated = True`. No external payment SDKs are used.
7. **Fail-Safe Live Layer**: Routing never blocks on external HTTP calls. Weather and live reports adjust weights only if available; on any network error or timeout, the system gracefully falls back to precomputed scores with zero latency impact.

---

## 4. Execution Phases (Roadmap)
- **Phase 1**: Data & Scoring Core (Database, OSM ingestion, feature computation, imputation, percentile normalization, confidence labeling).
- **Phase 2**: Routing Engine (Scoring profiles, cost function with lambda slider, Dijkstra/A*, detour cap, worst-segment penalty, tests).
- **Phase 3**: Consumer API, Leaflet UI & Feedback Loop (Endpoints, interactive Leaflet map, plain-language explanations, user report snapping/corroboration).
- **Phase 4**: Time-of-day, Verification & Live Layer (Time band weights, cross-source verification, Open-Meteo weather adapter with fail-safe fallback).
- **Phase 5**: Business Layer & Security (Plans, hashed API keys, middleware rate limiting, quotas, usage events, signed webhooks).
- **Phase 6**: Dashboards & Invoicing (City dashboard, fleet CSV tool, admin analytics, simulated invoice engine).
- **Phase 7**: Scalability, CLI, Benchmarking & Packaging (`add_city` CLI, Docker, sensitivity/benchmark endpoints, complete documentation).
- **Phase 8**: Final Audit & Verification (Rigorous checklist validation, test suite re-run, comprehensive proof report).
