import logging
from datetime import datetime
from pathlib import Path

from hdx.api.configuration import Configuration
from hdx.utilities.retriever import Retrieve

logger = logging.getLogger(__name__)


class APIRetriever:
    def __init__(self, configuration: Configuration, retriever: Retrieve):
        self._configuration = configuration
        self._retriever = retriever
        self._glofas_url = configuration["glofas_url"]
        self._gfm_url = configuration["gfm_url"]
        self._bbox = configuration["bbox"]
        self._width = configuration["width"]
        self._height = configuration["height"]

    def _process_wms(
        self,
        source_url: str,
        layer_name: str,
        time_str: str | None,
        filename: str,
        out_format: str,
    ) -> tuple[Path | None, str]:
        """Downloads WMS GeoTIFF. Omits the TIME parameter when time_str is None."""
        url = (
            f"{source_url}?"
            f"LAYERS={layer_name}&"
            f"FORMAT={out_format}&"
            "TRANSPARENT=true&SINGLETILE=false&SERVICE=WMS&"
            "VERSION=1.3.0&REQUEST=GetMap&STYLES=&CRS=EPSG:4326&"
            f"BBOX={self._bbox}&"
            f"WIDTH={self._width}&"
            f"HEIGHT={self._height}"
        )
        if time_str is not None:
            url += f"&TIME={time_str}"
        logger.info(f"Requesting WMS layer: {filename}")
        return self._retriever.download_file(url, filename=filename), url

    @staticmethod
    def get_metadata(info: dict, today: datetime, layer_key: str) -> tuple:
        resource_name = info["resource_name"]
        ext = info["ext"]
        label = layer_key
        start_date = today
        end_date = today
        date_str = None
        filename = f"{resource_name}_{layer_key}.{ext}"
        return start_date, end_date, date_str, "current", label, filename

    def process(self, today: datetime) -> dict:
        downloaded_files = {}
        datasets = self._configuration.get("datasets", {})

        for data_type, info in datasets.items():
            downloaded_files[data_type] = {}
            source = info.get("source", "glofas")
            source_url = self._glofas_url if source == "glofas" else self._gfm_url

            for layer_key, layer_dict in info["layers"].items():
                start_date, end_date, date_str, time_desc, label, filename = (
                    self.get_metadata(info, today, layer_key)
                )
                path, url = self._process_wms(
                    source_url,
                    layer_dict["layer"],
                    date_str,
                    filename,
                    info["format"],
                )
                if path:
                    downloaded_files[data_type][label] = {
                        "path": path,
                        "start_date": start_date,
                        "end_date": end_date,
                        "layer_desc": layer_dict["description"],
                        "time_desc": time_desc.replace("_", " "),
                        "ext": info["ext"],
                        "download_url": url,
                    }

        return downloaded_files
