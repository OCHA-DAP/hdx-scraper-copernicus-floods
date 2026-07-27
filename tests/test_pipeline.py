"""Tests for Copernicus Floods Pipeline"""

from pathlib import Path

from hdx.utilities.dateparse import parse_date
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from hdx.scraper.copernicus.floods.api_retriever import APIRetriever
from hdx.scraper.copernicus.floods.pipeline import Pipeline

_GLOFAS_WMS_BASE = (
    "https://ows.globalfloods.eu/glofas-ows/ows.py?"
    "LAYERS={layer}&FORMAT=image/tiff&TRANSPARENT=true&SINGLETILE=false"
    "&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:4326"
    "&BBOX=-90.0,-180.0,90.0,180.0&WIDTH=3600&HEIGHT=1800"
)
_GFM_WMS_BASE = (
    "https://geoserver.gfm.eodc.eu/geoserver/gfm/wms?"
    "LAYERS={layer}&FORMAT=image/geotiff&TRANSPARENT=true&SINGLETILE=false"
    "&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:4326"
    "&BBOX=-90.0,-180.0,90.0,180.0&WIDTH=3600&HEIGHT=1800"
)


class TestCopernicusFloods:
    def test_pipeline(self, configuration, input_dir):
        """Test the API Retriever and Pipeline logic end-to-end."""
        with temp_dir("TestCopernicusFloods") as temp_folder:
            with Download() as downloader:
                retriever = Retrieve(
                    downloader=downloader,
                    fallback_dir=temp_folder,
                    saved_dir=input_dir,
                    temp_dir=temp_folder,
                    save=False,
                    use_saved=True,
                )

                today = parse_date("2026-04-01")

                # 1. Test APIRetriever
                api_retriever = APIRetriever(configuration, retriever)
                downloaded_files = api_retriever.process(today=today)

                assert "glofas_forecast" in downloaded_files
                assert "glofas_initial_conditions" in downloaded_files
                assert "gfm_monitoring" in downloaded_files

                # --- GloFAS Forecast ---
                glofas_forecast_files = downloaded_files["glofas_forecast"]
                assert len(glofas_forecast_files) == 7

                assert glofas_forecast_files["flood_summary_1_3"] == {
                    "download_url": _GLOFAS_WMS_BASE.format(layer="sumAL41EGE"),
                    "end_date": today,
                    "ext": "geotiff",
                    "layer_desc": "Flood Summary Days 1-3",
                    "path": Path(
                        "saved_data/copernicus_glofas_forecast_flood_summary_1_3.geotiff"
                    ),
                    "start_date": today,
                    "time_desc": "current",
                }

                assert glofas_forecast_files["rapid_flood_mapping"] == {
                    "download_url": _GLOFAS_WMS_BASE.format(layer="RapidFloodMapping"),
                    "end_date": today,
                    "ext": "geotiff",
                    "layer_desc": "Rapid Flood Mapping - Estimated Flood Extent (Experimental)",
                    "path": Path(
                        "saved_data/copernicus_glofas_forecast_rapid_flood_mapping.geotiff"
                    ),
                    "start_date": today,
                    "time_desc": "current",
                }

                assert glofas_forecast_files["rapid_impact_assessment"] == {
                    "download_url": _GLOFAS_WMS_BASE.format(
                        layer="RapidImpactAssessment"
                    ),
                    "end_date": today,
                    "ext": "geotiff",
                    "layer_desc": "Rapid Impact Assessment - Population and Land Use (Experimental)",
                    "path": Path(
                        "saved_data/copernicus_glofas_forecast_rapid_impact_assessment.geotiff"
                    ),
                    "start_date": today,
                    "time_desc": "current",
                }

                # --- GloFAS Initial Conditions ---
                glofas_initial_files = downloaded_files["glofas_initial_conditions"]
                assert len(glofas_initial_files) == 6

                assert glofas_initial_files["precip_3d"] == {
                    "download_url": _GLOFAS_WMS_BASE.format(layer="precip3Days"),
                    "end_date": today,
                    "ext": "geotiff",
                    "layer_desc": "3-Day Accumulated Precipitation",
                    "path": Path(
                        "saved_data/copernicus_glofas_initial_conditions_precip_3d.geotiff"
                    ),
                    "start_date": today,
                    "time_desc": "current",
                }

                assert glofas_initial_files["soil_moisture_anomaly"] == {
                    "download_url": _GLOFAS_WMS_BASE.format(
                        layer="soilMoistureInstAnomaly"
                    ),
                    "end_date": today,
                    "ext": "geotiff",
                    "layer_desc": "Instantaneous Soil Moisture Anomaly",
                    "path": Path(
                        "saved_data/copernicus_glofas_initial_conditions_soil_moisture_anomaly.geotiff"
                    ),
                    "start_date": today,
                    "time_desc": "current",
                }

                # --- GFM Monitoring ---
                gfm_monitoring_files = downloaded_files["gfm_monitoring"]
                assert len(gfm_monitoring_files) == 5

                _wms_gfm = _GFM_WMS_BASE  # no TIME parameter

                assert gfm_monitoring_files["observed_flood_extent"] == {
                    "download_url": _wms_gfm.format(layer="observed_flood_extent"),
                    "end_date": today,
                    "ext": "geotiff",
                    "layer_desc": "Observed Flood Extent",
                    "path": Path(
                        "saved_data/copernicus_gfm_monitoring_observed_flood_extent.geotiff"
                    ),
                    "start_date": today,
                    "time_desc": "current",
                }

                assert gfm_monitoring_files["likelihood_values"] == {
                    "download_url": _wms_gfm.format(layer="uncertainty_values"),
                    "end_date": today,
                    "ext": "geotiff",
                    "layer_desc": "Flood Detection Likelihood Values",
                    "path": Path(
                        "saved_data/copernicus_gfm_monitoring_likelihood_values.geotiff"
                    ),
                    "start_date": today,
                    "time_desc": "current",
                }

                # 2. Test Pipeline Dataset Generation
                pipeline = Pipeline(configuration, downloaded_files)

                # --- GloFAS Forecast Dataset ---
                glofas_forecast_dataset, glofas_forecast_showcase = (
                    pipeline.generate_dataset_and_showcase(
                        "glofas_forecast", today=today
                    )
                )
                assert glofas_forecast_showcase is None

                assert (
                    glofas_forecast_dataset["name"]
                    == "copernicus-glofas-flood-forecast"
                )
                assert (
                    glofas_forecast_dataset["title"] == "Global - GloFAS Flood Forecast"
                )
                assert glofas_forecast_dataset["dataset_date"] == (
                    "[2026-04-01T00:00:00 TO 2026-04-01T23:59:59]"
                )
                assert glofas_forecast_dataset["subnational"] == "1"
                assert glofas_forecast_dataset["groups"] == [{"name": "world"}]
                assert glofas_forecast_dataset["tags"] == [
                    {
                        "name": "climate hazards",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "flooding",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "forecasting",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "hazards and risk",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ]

                gf_resources = glofas_forecast_dataset.get_resources()
                assert len(gf_resources) == 7

                for res in gf_resources:
                    assert res["format"] == "geotiff"

                assert gf_resources[0] == {
                    "dataset_preview_enabled": "False",
                    "description": "GeoTIFF representing Flood Summary Days 1-3 (1 Apr 2026)",
                    "format": "geotiff",
                    "name": "copernicus_glofas_forecast_flood_summary_1_3.geotiff",
                }
                assert gf_resources[5] == {
                    "dataset_preview_enabled": "False",
                    "description": "GeoTIFF representing Rapid Flood Mapping - Estimated Flood "
                    "Extent (Experimental) (1 Apr 2026)",
                    "format": "geotiff",
                    "name": "copernicus_glofas_forecast_rapid_flood_mapping.geotiff",
                }
                assert gf_resources[6] == {
                    "dataset_preview_enabled": "False",
                    "description": "GeoTIFF representing Rapid Impact Assessment - Population and "
                    "Land Use (Experimental) (1 Apr 2026)",
                    "format": "geotiff",
                    "name": "copernicus_glofas_forecast_rapid_impact_assessment.geotiff",
                }

                # --- GloFAS Initial Conditions Dataset ---
                glofas_initial_dataset, glofas_initial_showcase = (
                    pipeline.generate_dataset_and_showcase(
                        "glofas_initial_conditions", today=today
                    )
                )
                assert glofas_initial_showcase is None

                assert (
                    glofas_initial_dataset["name"]
                    == "copernicus-glofas-initial-conditions"
                )
                assert (
                    glofas_initial_dataset["title"]
                    == "Global - GloFAS Initial Conditions"
                )
                assert glofas_initial_dataset["dataset_date"] == (
                    "[2026-04-01T00:00:00 TO 2026-04-01T23:59:59]"
                )
                assert glofas_initial_dataset["tags"] == [
                    {
                        "name": "climate hazards",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "flooding",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "hazards and risk",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ]

                gi_resources = glofas_initial_dataset.get_resources()
                assert len(gi_resources) == 6

                for res in gi_resources:
                    assert res["format"] == "geotiff"
                assert gi_resources[0] == {
                    "dataset_preview_enabled": "False",
                    "description": "GeoTIFF representing 3-Day Accumulated Precipitation (1 Apr 2026)",
                    "format": "geotiff",
                    "name": "copernicus_glofas_initial_conditions_precip_3d.geotiff",
                }

                # --- GFM Monitoring Dataset ---
                gfm_dataset, gfm_showcase = pipeline.generate_dataset_and_showcase(
                    "gfm_monitoring", today=today
                )
                assert gfm_showcase is None

                assert gfm_dataset["name"] == "copernicus-gfm-flood-monitoring"
                assert gfm_dataset["title"] == "Global - GFM Flood Monitoring"
                assert gfm_dataset["dataset_date"] == (
                    "[2026-04-01T00:00:00 TO 2026-04-01T23:59:59]"
                )
                assert gfm_dataset["tags"] == [
                    {
                        "name": "climate hazards",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "flooding",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                    {
                        "name": "hazards and risk",
                        "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                    },
                ]

                gfm_resources = gfm_dataset.get_resources()
                assert len(gfm_resources) == 5

                for res in gfm_resources:
                    assert res["format"] == "geotiff"
                    assert "(1 Apr 2026)" in res["description"]

                assert gfm_resources[0] == {
                    "dataset_preview_enabled": "False",
                    "description": "GeoTIFF representing Observed Flood Extent (1 Apr 2026)",
                    "format": "geotiff",
                    "name": "copernicus_gfm_monitoring_observed_flood_extent.geotiff",
                }
                assert gfm_resources[4] == {
                    "dataset_preview_enabled": "False",
                    "description": "GeoTIFF representing Flood Detection Likelihood Values "
                    "(1 Apr 2026)",
                    "format": "geotiff",
                    "name": "copernicus_gfm_monitoring_likelihood_values.geotiff",
                }
