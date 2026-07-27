# CLAUDE.md

## Project Overview

**hdx-scraper-copernicus-floods** scrapes flood data from the Copernicus GloFAS and GFM APIs
and uploads it to the UN Humanitarian Data Exchange (HDX) platform. It produces three datasets:

- **copernicus-glofas-flood-forecast** — flood summary and return-period exceedance layers from GloFAS (WMS/GeoTIFF, 1-day forecast)
- **copernicus-glofas-initial-conditions** — hydrometeorological initial conditions from GloFAS (WMS/GeoTIFF, current day)
- **copernicus-gfm-flood-monitoring** — near-real-time Sentinel-1 flood observations from GFM (WMS/GeoTIFF, latest available)

## Key Files

- `src/hdx/scraper/copernicus/floods/__main__.py` — orchestration entry point (`main()`)
- `src/hdx/scraper/copernicus/floods/api_retriever.py` — Copernicus WMS API client (`APIRetriever` class)
- `src/hdx/scraper/copernicus/floods/pipeline.py` — HDX dataset/resource generation (`Pipeline` class)
- `src/hdx/scraper/copernicus/floods/config/project_configuration.yaml` — datasets, layers, API endpoints
- `src/hdx/scraper/copernicus/floods/config/hdx_dataset_static.yaml` — static metadata applied to all datasets

## Running

```bash
uv run python -m hdx.scraper.copernicus.floods
```

Requires these files in `$HOME`:
- `.hdx_configuration.yaml` — HDX API key and site config
- `.useragents.yaml` — user agent config with key `hdx-scraper-copernicus-floods`

Or set environment variables: `HDX_KEY`, `HDX_SITE`, `USER_AGENT`, `EXTRA_PARAMS`.

Development flags (passed to `main()`):
- `save=True` — save downloaded API responses to `saved_data/` instead of `/tmp`
- `use_saved=True` — load from `saved_data/` instead of calling the API

## Testing

```bash
pytest
# or
uv run pytest
```

Tests live in `tests/test_pipeline.py`. The test uses `use_saved=True` with a fixed date (`2026-04-01`) for deterministic output against locally saved API responses in `saved_data/`.

To update expected outputs after intentional changes, update the assertions in `test_pipeline.py` and replace any saved input files.

## Code Style

- Formatted with `ruff` via pre-commit hooks. After changing any Python code, run:

```bash
pre-commit run --all-files
```

- Python ≥ 3.13

## API Sources

- **GloFAS WMS**: `https://ows.globalfloods.eu/glofas-ows/ows.py` (WMS 1.1.1, EPSG:4326, `image/tiff`)
- **GFM WMS**: `https://geoserver.gfm.eodc.eu/geoserver/gfm/wms` (WMS 1.1.1, EPSG:4326, `image/geotiff`)

GFM layers have no TIME dimension — the service returns the latest Sentinel-1 observation.
GloFAS forecast layers use a single date (tomorrow); initial condition layers use a date range.

## Collaboration Style

- Be objective, not agreeable. Act as a partner, not a sycophant. Push back when you disagree, flag tradeoffs honestly, and don't sugarcoat problems.
- Keep explanations brief and to the point.
- Don't rely on recalled knowledge for facts that could be stale (API behaviour, library versions, external systems). Search or read the actual source first. If you lack verified information, say so rather than speculate.

## Scope of Changes

When fixing a bug or addressing PR feedback, change only what is necessary to resolve the specific issue. Do not refactor surrounding code, rename variables, adjust formatting, or make improvements in the same commit unless they are directly required by the fix. Unrelated changes obscure the intent of the fix and complicate review and blame.
