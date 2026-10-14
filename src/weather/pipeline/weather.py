from typing import Any

import time
import psycopg
import requests

URL = "https://api.open-meteo.com/v1/forecast"

params: dict[str, Any] = {
    "latitude": 40,
    "longitude": 66,
    "current": "temperature_2m,relative_humidity_2m",
}


def fetch_weather() -> dict[str, Any] | None:
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

            print(f"HTTP {status_code}. " f"Retrying after attempt {attempt}...")

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as err:
            if attempt == max_attempts:
                raise

            print(f"Network error: {err}. " f"Retrying after attempt {attempt}...")

        delay = 2 ** (attempt - 1)
        time.sleep(delay)


def save_weather(record: dict[str, Any]):
    with psycopg.connect(
        "dbname=weather_pipeline user=postgres password=3211 host=localhost"
    ) as conn:
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


def extract_weather(data: dict[str, Any]) -> dict[str, Any]:
    current = data["current"]

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    recorded_at = current["time"]

    if temperature is None:
        raise ValueError("Temperature is missing")

    if humidity is None:
        raise ValueError("Humidity is missing")

    if recorded_at is None:
        raise ValueError("Observation timestamp is missing")

    return {
        "temperature": temperature,
        "humidity": humidity,
        "recorded_at": recorded_at,
    }


if __name__ == "__main__":
    data = fetch_weather()

    if data is not None:
        record = extract_weather(data)
        save_weather(record)

        print("Weather data saved!")

    else:
        print("Data is invalid")
