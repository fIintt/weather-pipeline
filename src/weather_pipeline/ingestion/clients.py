import logging
import time
from typing import Any

import requests

from weather_pipeline.config import API_TIMEOUT, API_URL

logger = logging.getLogger(__name__)


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

    params: dict[str, Any] = {
        "latitude": 40,
        "longitude": 66,
        "current": "temperature_2m,relative_humidity_2m",
    }

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=API_TIMEOUT)
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
