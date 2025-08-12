import os
from dotenv import load_dotenv
import clickhouse_connect

load_dotenv()

client = clickhouse_connect.get_client(
    host=os.getenv("CLICKHOUSE_HOST"),
    port=int(os.getenv("CLICKHOUSE_PORT")),
    username=os.getenv("CLICKHOUSE_USER"),
    password=os.getenv("CLICKHOUSE_PASSWORD"),
    database=os.getenv("CLICKHOUSE_DB"),
)

def create_table():
    client.command("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_number UInt32,
            buyer_name String,
            buyer_phone String,
            seller_name String,
            payment_status String,
            mode_of_payment String,
            date_sold Date,
            date_of_payment Nullable(Date),
            remarks String
        )
        ENGINE = MergeTree()
        ORDER BY ticket_number
    """)
