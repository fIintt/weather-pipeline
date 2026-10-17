from typing import Any

import psycopg

from weather_pipeline.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def load_weather(record: dict[str, Any]) -> bool:
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


def load_weather_archive(records: list[dict[str, Any]]) -> int:
    if not records:
        return 0

    values: list[tuple[Any, ...]] = [
        (record["recorded_at"], record["temperature"], record["humidity"])
        for record in records
    ]

    with psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO weather_archive_data 
                    (recorded_at, temperature, humidity)
                VALUES 
                    (%s, %s, %s)
                ON CONFLICT (recorded_at) DO NOTHING
                """,
                values,
                returning=False,
            )
        
            return cursor.rowcount
