import mysql.connector
def get_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            username="root",
            password="Mane@1362",
            database="CANTEEN_APP"
        )
        return connection
    except Exception as e:
        print("Database connection failed:", e)
        return None