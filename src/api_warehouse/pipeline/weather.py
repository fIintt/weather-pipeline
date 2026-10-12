from typing import Any

import psycopg
import requests

URL = "https://api.open-meteo.com/v1/forecast"

params: dict[str, Any] = {
    "latitude": 21.0285,
    "longitude": 105.8542,
    "current": "temperature_2m,relative_humidity_2m",
}


def fetch_weather():
    response = requests.get(URL, params=params)
    response.raise_for_status()

    return response.json()


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

    record = extract_weather(data)

    save_weather(record)
    
    print("Weather data saved!")
