import logging
from datetime import datetime, timedelta
from pathlib import Path

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.data.resource import Resource
from hdx.data.showcase import Showcase

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, configuration: Configuration, downloaded_files: dict):
        self._configuration = configuration
        self._downloaded_files = downloaded_files

    @staticmethod
    def generate_resource(
        resource_name: str, resource_description: str, file_path: Path, extension: str
    ) -> Resource:
        resource = Resource(
            {
                "name": resource_name,
                "description": resource_description,
            }
        )

        ext_lower = extension.lower()
        fmt_map = {
            "geojson": "geojson",
            "geotiff": "geotiff",
            "zip": "zipped shapefile",
        }
        if ext_lower in fmt_map:
            resource.set_format(fmt_map[ext_lower])

        resource.set_file_to_upload(file_path)
        return resource

    def generate_dataset_and_showcase(
        self, data_type: str, today: datetime
    ) -> tuple[Dataset, Showcase | None] | None:
        dataset_info = self._configuration["datasets"].get(data_type)
        if not dataset_info:
            return None

        logger.info(f"{data_type}: Generating dataset...")
        files = self._downloaded_files.get(data_type, {})

        if not files:
            logger.error(f"{data_type}: No data available!")
            return None

        min_start_date = min(layer["start_date"] for layer in files.values())
        max_end_date = max(layer["end_date"] for layer in files.values())
        url = next(iter(files.values()))["download_url"]
        start_date = min_start_date.strftime("%Y-%m-%d")
        end_date = max_end_date.strftime("%Y-%m-%d")
        logger.info(
            f"Using dates {start_date} to {end_date} for {data_type}. Example url {url}."
        )

        dataset = Dataset(
            {
                "name": dataset_info["name"],
                "title": dataset_info["title"],
                "notes": dataset_info.get("notes", ""),
            }
        )
        dataset.set_time_period(start_date, end_date)

        tags = dataset_info["tags"]
        dataset.add_tags(tags)
        dataset.set_subnational(True)
        dataset.add_other_location("world")

        for label, resource_info in files.items():
            file_path = resource_info["path"]
            res_start_date = resource_info["start_date"]
            res_end_date = resource_info["end_date"]
            layer_desc = resource_info["layer_desc"]
            time_desc = resource_info["time_desc"]
            ext = resource_info["ext"]

            start_str = res_start_date.strftime("%d %b %Y").lstrip("0")
            end_str = res_end_date.strftime("%d %b %Y").lstrip("0")
            date_range = (
                f"({start_str})" if start_str == end_str else f"({start_str}-{end_str})"
            )

            fmt_label = {"geojson": "GeoJSON", "geotiff": "GeoTIFF"}.get(
                ext.lower(), "Data"
            )
            time_part = f" {time_desc}" if time_desc != "current" else ""
            res_desc = f"{fmt_label} representing {layer_desc}{time_part} {date_range}"

            dataset.add_update_resource(
                self.generate_resource(file_path.name, res_desc, file_path, ext)
            )

        showcase = None
        showcase_info = dataset_info.get("showcase")
        if showcase_info:
            forecast_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            today_str = today.strftime("%Y-%m-%d")
            map_url = showcase_info["url_template"].format(
                forecast_date=forecast_date, today=today_str
            )
            showcase = Showcase(
                {
                    "name": f"{dataset_info['name']}-showcase",
                    "title": f"{dataset_info['title']} Interactive Map",
                    "notes": showcase_info["notes"],
                    "url": map_url,
                    "image_url": showcase_info["image_url"],
                }
            )
            showcase.add_tags(tags)

        dataset.preview_off()
        return dataset, showcase
