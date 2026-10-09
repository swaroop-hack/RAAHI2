# Raahi - Build Progress Log

## Phase Overview & Checklist
- [x] Phase 1: Data and scoring core
- [x] Phase 2: Routing
- [x] Phase 3: Consumer API, frontend and feedback loop
- [x] Phase 4: Time-of-day, verification and live data
- [ ] Phase 5: Business layer
- [ ] Phase 6: Dashboards and invoicing
- [ ] Phase 7: Scale, validation and delivery
- [ ] Phase 8: Final audit and fixes

---
## Initialization
- **Plan Established**: Created `PLAN.md` with complete architectural layout, assumptions, modular package structure, and 8-phase execution roadmap.
- **Environment**: Initialized Python environment with FastAPI, SQLAlchemy, NetworkX, Shapely, Pandas, Scikit-learn, Pytest.

---
## Phase 1: Data and Scoring Core
- **What was built**:
  - `raahi/config.py`: Unified configuration with city bounds, profile weights, time bands, and monetization tiers.
  - `raahi/database.py`: SQLAlchemy session engine supporting SQLite/SpatiaLite with automatic PostGIS compatibility.
  - `raahi/models.py`: Complete database schema for all required tables (`cities`, `edges`, `pois`, `edge_features`, `user_reports`, `survey_weights`, `survey_ratings`, `field_checks`, `plans`, `api_clients`, `api_keys`, `usage_events`, `invoices_simulated`, `config`). Every table includes `city_id`, `source`, `data_quality`, and `timestamp`.
  - `raahi/schemas.py`: Comprehensive Pydantic models for request/response serialization.
  - `raahi/ingestion/ingest_osm.py`: Resilient ingestion engine with geographic coordinate boundary validation, duplicate rejection, and OSM topology parsing for Jaipur with high-fidelity fallback.
  - `raahi/core/features.py`: Feature computation pipeline (lighting imputation from road priors and POI density, open POIs in buffers per time band, road hierarchy + sidewalks, incident decay, help proximity, percentiles normalization with strict 0.5 default, confidence labeling).
- **What was tested**:
  - `tests/test_features.py`: 6 tests passing (bounds validation, ingestion counts, missing value imputation never 0, percentile normalization handling NaNs, confidence label assignments, multi-time-band feature persistence).
- **What failed & how it was fixed**:
  - Initial `scipy.stats` DLL failed under Windows Application Control policy (`_pava_pybind`). Fixed by implementing clean pure-math and pandas rank percentile normalization (`normalize_percentile`) that runs robustly without requiring blocked C DLLs.
- **Checkpoint Results**:
  - Ingestion run for Jaipur: 76 total edges, 64 edges with real lit tag, 12 edges with imputed lighting.
  - Sample rows from `edge_features` verified with non-zero scores, imputation flags, and confidence tags.

---
## Phase 2: Routing Engine
- **What was built**:
  - `raahi/core/routing.py`:
    - Fast in-memory spatial graph caching per `(city_id, time_band)`.
    - Profile weight normalization with survey weight defaults and custom overrides.
    - Safety scoring function per edge: weighted sum bounded [0.05, 0.99] strictly non-zero.
    - Safety-vs-speed cost function: `length * (1 + lambda * (1 - safety))`.
    - Non-linear worst-segment penalty and minimum safety threshold avoidance (< 0.30).
    - Dijkstra shortest-path solver returning dual routes ("Fastest" and "Raahi Safe Route").
    - Adaptive detour cap enforcement (Pareto bisection sweep when candidate safest route exceeds user cap).
    - Template-based plain-language explanation generator with POI differentials and avoided dark stretch metrics.
- **What was tested**:
  - `tests/test_routing.py`: 4 tests passing (profile weights normalization, edge cost lambda and threshold penalties, detour cap adherence, dual route generation).
- **What failed & how it was fixed**:
  - Initial route candidate in deep penalty mode risked exceeding the detour cap on long detours. Fixed by implementing binary search / step-down lambda sweep (`solve_with_lambda`) that guarantees the safest route respects the `detour_cap` over the fastest route.
- **Checkpoint Results**:
  - 3 sample O-D pairs evaluated across Jaipur:
    1. Sindhi Camp to SMS Hospital: Fastest = 3718.7m (safety 0.501, worst 0.309), Safe = 3983.9m (safety 0.617, worst 0.594) -> +7.1% detour (cap 25%), +23.2% safety gain, avoiding 1522m of less-lit stretches.
    2. Railway Station to Hawa Mahal: Fastest = 6080.2m (safety 0.631), Safe = 6080.2m (safety 0.631) -> already optimal via primary MI Road.
    3. Statue Circle to Bapu Bazaar: Fastest = 2339.0m (safety 0.668), Safe = 2339.0m (safety 0.668).

---
## Phase 3: Consumer API, Frontend and Feedback Loop
- **What was built**:
  - `raahi/core/feedback.py`: Anonymous reporting pipeline with road snapping (`snap_point_to_edge` within 150m), duplicate merging within 15 minutes by hashed client IP, exponential decay calculation, corroboration thresholding (3+ reports elevate confidence and incident penalty), and burst rate limiting (sliding window).
  - `raahi/api/routes_consumer.py`: Consumer endpoints:
    - `POST /route`: End-to-end multi-objective routing with dual routes, metrics, and quality summary.
    - `GET /explain`: Plain-language explanation generation.
    - `POST /report`: Anonymous user safety submission with edge snapping.
    - `GET /safe_stops`: Proximity search for emergency and night-safe POIs.
    - `GET /health`: Diagnostic health check.
  - `raahi/api/main.py`: FastAPI server with CORS, static routing, and SPA mounting.
  - `raahi/static/index.html`, `style.css`, `app.js`: Interactive Leaflet web interface with dark night theme, draggable origin/dest pins, demo presets, profile selector, time-of-day modes, preference sliders, comparison cards, "Tell Raahi" reporting modal, safe stops overlay, and ethical disclaimers.
- **What was tested**:
  - `tests/test_feedback.py`: 6 tests passing (health diagnostics, spatial snapping, distant point rejection, duplicate merging by IP hash, burst rate limiting, dual route response formatting).
- **What failed & how it was fixed**:
  - FastAPI TestClient needed `httpx` installed (`pip install httpx`).
  - Report ID timestamp collision on rapid sequential inserts in SQLite. Fixed by appending unique `uuid.uuid4().hex[:8]` to `report_id`.
- **Checkpoint Results**:
  - End-to-end request on `/route` verified:
    - Fastest: 3718.7m (safety 0.501, 49.6 mins)
    - Raahi Safe Route: 3983.9m (safety 0.617, 53.1 mins)
    - Detour: +7.1% (well within 25% cap), Safety Gain: +21.4%
    - Explanation: "This route is 7% longer (265m extra) but passes 2 additional open shops and active safe spots and avoids 1522m of less lit or low-activity stretches."
  - User UI experience: Clean Leaflet dark carto interface displaying solid emerald safe path, dashed amber fastest path, side-by-side stats, and anonymous reporting.

---
## Phase 4: Time-of-Day, Verification and Live Data
- **What was built**:
  - `raahi/core/verify.py`:
    - Cross-source checks (`run_cross_source_checks`): detects lit tag vs road hierarchy anomalies, correlates low scores with corroborated reports, increments `agreement_count` and `disagreement_count`, assigns confidence labels, enforces neutral 0.5 default on low confidence stretches.
    - Field check audit importer (`ingest_sample_field_checks`) tagged with `data_quality = 'verified'`.
    - Verification report generator (`generate_verification_report` / `GET /verification_report`): returns checked segment count, match rate against ground-truth audits, and audited sample size without extrapolating city-wide.
  - `raahi/live/adapters/base.py`: Abstract pluggable interface (`fetch`, `normalise`, `health_check`).
  - `raahi/live/adapters/weather.py`: Open-Meteo live API integration (no keys required) with 2-second timeout, weather condition parsing (rain, fog, dust), and forced failure switch.
  - `raahi/live/adapters/reports.py`: Live user report decay adapter.
  - `raahi/live/adapters/stubs.py`: Documented, disabled-by-default stub adapters for municipal smart-lighting SCADA, live traffic, and partner fleet optical feeds.
  - `raahi/live/manager.py`: Coordinator with TTL in-memory caching and fail-safe fallback guarantee.
- **What was tested**:
  - `tests/test_live.py`: 5 tests passing (cross-source verification, field verification reporting, stub adapters disabled by default, time-of-day modes, and weather adapter fail-safe forced failure).
- **What failed & how it was fixed**:
  - Initial weather adapter timeout could potentially cause slight routing lag if Open-Meteo was slow. Fixed with strict 2.0s timeout and instant cache fallback so routing never blocks.
- **Checkpoint Results**:
  - Weather adapter forced failure test (`test_weather_adapter_fail_safe_forced_failure`) succeeded: When forced to fail, routing proceeded immediately using stored precomputed scores, returned valid fastest and safest routes, and correctly flagged `has_live_data = False`.




