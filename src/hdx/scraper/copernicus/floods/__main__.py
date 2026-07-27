#!/usr/bin/python
"""
Top level script. Calls API retrieval and pipeline generation functions
to create and upload datasets to HDX.
"""

import logging
from os.path import expanduser, join

from hdx.api.configuration import Configuration
from hdx.data.user import User
from hdx.facades.infer_arguments import facade
from hdx.utilities.dateparse import now_utc
from hdx.utilities.downloader import Download
from hdx.utilities.path import (
    script_dir_plus_file,
    wheretostart_tempdir_batch,
)
from hdx.utilities.retriever import Retrieve

from hdx.scraper.copernicus.floods._version import __version__
from hdx.scraper.copernicus.floods.api_retriever import APIRetriever
from hdx.scraper.copernicus.floods.pipeline import Pipeline

logger = logging.getLogger(__name__)

_LOOKUP = "hdx-scraper-copernicus-floods"
_SAVED_DATA_DIR = "saved_data"  # Keep in repo to avoid deletion in /tmp
_UPDATED_BY_SCRIPT = "HDX Scraper: Copernicus Floods"


def main(
    save: bool = False,
    use_saved: bool = False,
) -> None:
    """Generate datasets and create them in HDX"""
    logger.info(f"##### {_LOOKUP} version {__version__} ####")
    configuration = Configuration.read()

    User.check_current_user_write_access("47677055-92e2-4f68-bf1b-5d570f27e791")

    with wheretostart_tempdir_batch(folder=_LOOKUP) as info:
        tempdir = info["folder"]
        with Download() as downloader:
            retriever = Retrieve(
                downloader=downloader,
                fallback_dir=tempdir,
                saved_dir=_SAVED_DATA_DIR,
                temp_dir=tempdir,
                save=save,
                use_saved=use_saved,
            )

            today = now_utc()
            # 1. Download the files (GeoTIFFs)
            apiretriever = APIRetriever(configuration, retriever)
            downloaded_files = apiretriever.process(today)

            # 2. Initialize the pipeline with the downloaded files
            pipeline = Pipeline(configuration, downloaded_files)

            # 3. Iterate through datasets defined in configuration
            static_yaml_by_source = {
                "glofas": script_dir_plus_file(
                    join("config", "hdx_dataset_static_glofas.yaml"), main
                ),
                "gfm": script_dir_plus_file(
                    join("config", "hdx_dataset_static_gfm.yaml"), main
                ),
            }
            for data_type in downloaded_files:
                result = pipeline.generate_dataset_and_showcase(data_type, today)

                if result:
                    dataset, showcase = result

                    source = configuration["datasets"][data_type]["source"]
                    dataset.update_from_yaml(static_yaml_by_source[source])

                    # Create or update the dataset on HDX
                    dataset.create_in_hdx(
                        remove_additional_resources=True,
                        match_resource_order=True,
                        updated_by_script=_UPDATED_BY_SCRIPT,
                        batch=info["batch"],
                    )

                    if showcase:
                        showcase.create_in_hdx()
                        showcase.add_dataset(dataset)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=_LOOKUP,
        project_config_yaml=script_dir_plus_file(
            join("config", "project_configuration.yaml"), main
        ),
    )
