import psycopg

conn = psycopg.connect(
    "dbname=weather_pipeline user=postgres password=3211 host=localhost"
)

print("connected")

conn.close()
