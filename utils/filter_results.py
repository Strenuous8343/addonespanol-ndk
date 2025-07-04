import re

from utils.filter.max_size_filter import MaxSizeFilter
from utils.filter.quality_exclusion_filter import QualityExclusionFilter

from utils.logger import setup_logger

logger = setup_logger(__name__)

quality_order = {"4k": 0, "1080p": 1, "720p": 2, "480p": 3}


def filter_items(items, media, config):
    filters = {
        "maxSize": MaxSizeFilter(config, media.type),  # Max size filtering only happens for movies
        "selectedQualityExclusion": QualityExclusionFilter(config),
    }
    for filter_name, filter_instance in filters.items():
        try:
            logger.info(f"Filtering by {filter_name}: " + str(config[filter_name]))
            items = filter_instance(items)
            logger.info(f"Item count changed to {len(items)}")
        except Exception as e:
            logger.error(f"Error while filtering by {filter_name}", exc_info=e)
    logger.info(f"Item count after filtering: {len(items)}")
    logger.info("Finished filtering torrents")

    return items
