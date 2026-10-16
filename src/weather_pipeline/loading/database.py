from typing import Any

import psycopg

from weather_pipeline.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def save_weather(record: dict[str, Any]) -> bool:
    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
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

            return cursor.rowcount == 1
