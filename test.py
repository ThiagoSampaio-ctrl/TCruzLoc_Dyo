import psycopg2

try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        database="DyO_TH_Log",
        user="postgres",
        password="123456"
    )

    print("CONEXÃO OK")

except Exception as e:
    print(type(e))
    print(e)