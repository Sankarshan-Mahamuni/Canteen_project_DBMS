from flask import Flask, render_template, request, url_for, redirect
from database import get_db

app = Flask(__name__)

@app.route('/register', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        name = request.form['name']
        PRN = request.form['PRN']
        email = request.form['email']
        department = request.form['department']
        phoneno = request.form['phoneno']
        wallet_balance = request.form['wallet_balance']

        db = get_db()
        if db is None:
            print("Failed to connect to the database.")
            return render_template('index.html', error="Database connection failed.")
        cur = db.cursor()
        try:
            cur.execute("""
                        INSERT INTO student(name, PRN, email, department, phone_no, wallet_balance)
                        VALUES (%s, %s, %s, %s, %s, %s);
                        """,
                        (name, PRN, email, department, phoneno, wallet_balance)
                        )
            db.commit()
            print("Data inserted successfully")
            return redirect(url_for('index'))
        except Exception as e:
            print(e)

    return render_template('index.html')

@app.route('/add_to_cart')
def add_to_cart():
    pass

@app.route('/')
def home():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM menu_items")
    data = cur.fetchall()
    categories = {"Fast Food": [],
                  "Nasta": [],
                  "Lunch": [],
                  "Beverages": []}
    for item in data:
        categories[item["CATEGORY"]].append(item)

    return render_template('home.html', data=categories)

if __name__ == "__main__":
    app.run(debug=True)