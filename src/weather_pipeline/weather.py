import logging
import os
from typing import Any

import time
from dotenv import load_dotenv
import psycopg
import requests

URL = "https://api.open-meteo.com/v1/forecast"

params: dict[str, Any] = {
    "latitude": 40,
    "longitude": 66,
    "current": "temperature_2m,relative_humidity_2m",
}

logging.basicConfig(
    level=logging.INFO,  # minimum level of severity (e.g. DEBUG (severity = 10) will not be displayed)
    format="%(asctime)s | %(levelname)s | %(filename)s | %(message)s",
    datefmt="%m/%d/%Y %I:%M %p",  # MM/DD/YYYY HH:MM AM/PM (e.g., 10/14/2026 06:04 PM)
)

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def fetch_weather() -> dict[str, Any]:
    max_attempts = 3
    retryable_status_codes = {
        408,
        429,
        500,
        502,
        503,
        504,
    }  # Set {} instead of Tuple () because of O(1) vs O(n) lookup time

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(URL, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as err:
            if hasattr(err, "response") and err.response is not None:
                status_code = err.response.status_code
            else:
                status_code = None

            if status_code not in retryable_status_codes:
                raise

            if attempt == max_attempts:
                raise

            logger.warning(
                f"HTTP {status_code}. " f"Retrying after attempt {attempt}..."
            )

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as err:
            if attempt == max_attempts:
                raise

            logger.warning(
                f"Network error: {err}. " f"Retrying after attempt {attempt}..."
            )

        delay = 2 ** (attempt - 1)
        time.sleep(delay)

    return {}


def save_weather(record: dict[str, Any]) -> bool:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO weather_data
                    (temperature, humidity, recorded_at)
                VALUES
                    (%s, %s, %s)
                ON CONFLICT (recorded_at) DO NOTHING
                """,
                (record["temperature"], record["humidity"], record["recorded_at"]),
            )

            return cursor.rowcount == 1


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


def run_pipeline():
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


if __name__ == "__main__":
    run_pipeline()
