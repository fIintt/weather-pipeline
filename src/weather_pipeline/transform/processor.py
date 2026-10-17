from typing import Any


def transform_weather(data: dict[str, Any]) -> dict[str, Any]:
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


def transform_weather_archive(data: dict[str, Any]) -> list[dict[str, Any]]:
    hourly = data["hourly"]

    times = hourly["time"]
    temperatures = hourly["temperature_2m"]
    humidities = hourly["relative_humidity_2m"]

    records: list[dict[str, Any]] = []

    for recorded_at, temperature, humidity in zip(
        times, temperatures, humidities, strict=True
    ):
        records.append(
            {
                "recorded_at": recorded_at,
                "temperature": temperature,
                "humidity": humidity,
            }
        )

    return records