import logging

import time
from typing import Literal
import psycopg
import requests

from weather_pipeline.ingestion.clients import extract_weather, extract_weather_archive
from weather_pipeline.loading.database import load_weather, load_weather_archive
from weather_pipeline.logging_config import configure_logging
from weather_pipeline.transform.processor import (
    transform_weather,
    transform_weather_archive,
)

logger = logging.getLogger(__name__)


def run_pipeline(
    pipeline_type: Literal["single", "batch"],
    start_date: str | None = None,
    end_date: str | None = None,
) -> None:
    if pipeline_type not in ("single", "batch"):
        raise ValueError(f"Unsupported pipeline type: {pipeline_type}")

    started_at = time.perf_counter()

    logger.info("Weather pipeline started.")

    try:
        if pipeline_type == "single":
            raw = extract_weather()
            record = transform_weather(raw)
            inserted = load_weather(record)

            if inserted:
                logger.info("New weather observation inserted.")
            else:
                logger.info("Observation already exists. Skipped.")

        elif pipeline_type == "batch":
            if start_date is None or end_date is None:
                raise ValueError(
                    "start_date and end_date are required for batch ingestion"
                )

            raw = extract_weather_archive(start_date, end_date)
            records = transform_weather_archive(raw)
            inserted = load_weather_archive(records)

            skipped = len(records) - inserted

            logger.info(
                "Batch completed: received=%s inserted=%s skipped=%s",
                len(records),
                inserted,
                skipped,
            )

        else:
            print("Invalid pipeline type.")

    except requests.exceptions.RequestException:
        logger.exception("API request failed")
        raise

    except KeyError, ValueError, TypeError:
        logger.exception("Weather data validation failed")
        raise

    except psycopg.OperationalError:
        logger.exception("Database connection/operation failed")
        raise

    except psycopg.DataError:
        logger.exception("Database rejected the data")
        raise

    except psycopg.Error:
        logger.exception("Miscellaneous database error")
        raise

    else:
        logger.info("Weather pipeline succeeded.")

    finally:
        elapsed = time.perf_counter() - started_at
        logger.info(f"Pipeline execution took {elapsed:.2f} seconds")


def main() -> None:
    configure_logging()

    pipeline_type = str(input("Choose pipeline type [single/batch]: "))

    if pipeline_type == "single":
        run_pipeline("single")
    elif pipeline_type == "batch":
        start_date = str(input("Specify START DATE (YY-MM-DD): "))
        end_date = str(input("Specify END DATE (YY-MM-DD): "))
        
        run_pipeline("batch", start_date, end_date)
    else:
        print("Invalid pipeline type.")


if __name__ == "__main__":
    main()
