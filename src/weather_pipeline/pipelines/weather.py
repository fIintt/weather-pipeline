import logging
from typing import Any

import time
import psycopg
import requests

from weather_pipeline.ingestion.clients import fetch_weather
from weather_pipeline.loading.database import save_weather
from weather_pipeline.logging_config import configure_logging

logger = logging.getLogger(__name__)


def extract_weather(data: dict[str, Any]) -> dict[str, Any]:
    current = data["current"]

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    recorded_at = current["time"]

    # In python, booleans are a subclass of int (True = 1, False = 0)
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise ValueError("Temperature must be numeric")

    if isinstance(humidity, bool) or not isinstance(humidity, (int, float)):
        raise ValueError("Humidity must be numeric")

    if not 0 <= humidity <= 100:
        raise ValueError("Humidity must be between 0 and 100")

    if not isinstance(recorded_at, str) or not recorded_at:
        raise ValueError("Invalid observation timestamp")

    return {
        "temperature": temperature,
        "humidity": humidity,
        "recorded_at": recorded_at,
    }


def run_pipeline() -> None:
    started_at = time.perf_counter()

    logger.info("Weather pipeline started.")

    try:
        data = fetch_weather()
        record = extract_weather(data)
        inserted = save_weather(record)

        if inserted:
            logger.info("New weather observation inserted.")
        else:
            logger.info("Observation already exists. Skipped.")

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
    run_pipeline()


if __name__ == "__main__":
    main()
