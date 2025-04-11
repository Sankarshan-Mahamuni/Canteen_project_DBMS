from database import get_db
conn=get_db()
cur=conn.cursor(dictionary=True)
cur.execute("select * from menu_items")
data=cur.fetchall()
print(data)