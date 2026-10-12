import logging
from pathlib import Path

from ingestion import load_raw_tables
from staging import build_staging_tables
from quality_checks import (
    run_pre_mart_quality_checks,
    run_post_mart_quality_checks,
    run_quality_warnings,
)
from marts import build_mart_tables


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("olist_pipeline")


def run_pipeline():

    logger.info("OLIST ANALYTICS PIPELINE STARTED")

    try:
        logger.info("STEP 1: Loading RAW tables")
        load_raw_tables()

        logger.info("STEP 2: Building STAGING tables")
        build_staging_tables()

        logger.info("STEP 3: Running PRE-MART DATA QUALITY checks")
        run_pre_mart_quality_checks()

        logger.info("STEP 4: Building MART tables")
        build_mart_tables()

        logger.info("STEP 5: Running POST-MART DATA QUALITY checks")
        run_post_mart_quality_checks()

        logger.info("STEP 6: Running DATA QUALITY warnings")
        run_quality_warnings()

        logger.info("OLIST ANALYTICS PIPELINE COMPLETED SUCCESSFULLY")

    except Exception as error:
        logger.exception("PIPELINE FAILED: %s", error)
        raise


if __name__ == "__main__":
    run_pipeline()