from flask import Flask, render_template, request, url_for, redirect, jsonify,session,flash
from database import get_db
import pandas as pd
from datetime import datetime

app = Flask(__name__)

app.secret_key="abc1245"

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

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    #print(request.form)  
    item_id = request.form['item_id']
    quantity = int(request.form['quantity'])
    print(f"Item ID: {item_id}, Quantity: {quantity}")  # Debug
    prn = session.get('PRN')
    if not prn:
        return jsonify({"error": "User not logged in"}), 401

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Fetch item details
    cur.execute("SELECT PRICE FROM MENU_ITEMS WHERE ITEM_ID = %s", (item_id,))
    item = cur.fetchone()
    if not item:
        return jsonify({"error": "Item not found"}), 404

    sub_total = item['PRICE'] * quantity

    # Create or update order
    cur.execute("SELECT ORDER_ID FROM ORDER_TABLE WHERE PRN = %s AND STATUS = FALSE", (prn,))
    order = cur.fetchone()
    if not order:
        cur.execute("""
            INSERT INTO ORDER_TABLE (PRN, COUNTER_ID, TOTAL_AMOUNT)
            VALUES (%s, 1, 0)
        """, (prn,))
        db.commit()
        order_id = cur.lastrowid
    else:
        order_id = order['ORDER_ID']

    # Add item to ORDER_ITEMS
    cur.execute("""
        INSERT INTO ORDER_ITEMS (ITEM_ID, ORDER_ID, QUANTITY, SUB_TOTAL)
        VALUES (%s, %s, %s, %s)
    """, (item_id, order_id, quantity, sub_total))

    # Update total amount in ORDER_TABLE
    cur.execute("""
        UPDATE ORDER_TABLE
        SET TOTAL_AMOUNT = TOTAL_AMOUNT + %s
        WHERE ORDER_ID = %s
    """, (sub_total, order_id))

    db.commit()
    cur.execute("SELECT * FROM menu_items")
    data = cur.fetchall()
    # print(data)  # Debug: Log the data being passed to the template
    categories = {"Fast Food": [],
                  "Nasta": [],
                  "Lunch": [],
                  "Beverages": []}
    for item in data:
        categories[item["CATEGORY"]].append(item)
    flash("item added to cart !")
    return render_template("home.html",data=categories)

@app.route('/view_cart')
def view_cart():
    prn = session.get('PRN')
    if not prn:
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Fetch cart items for the logged-in user
    cur.execute(f"""
        SELECT M.NAME, SUM(O.QUANTITY) AS QUANTITY, SUM(O.SUB_TOTAL) AS TOTAL
        FROM MENU_ITEMS M
        INNER JOIN ORDER_ITEMS O ON M.ITEM_ID = O.ITEM_ID
        INNER JOIN ORDER_TABLE OT ON O.ORDER_ID = OT.ORDER_ID
        WHERE OT.PRN = %s AND OT.STATUS = FALSE
        GROUP BY O.ITEM_ID;
    """, (prn,))

    items = cur.fetchall()
    return render_template("view_cart.html", items=items)

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    prn = request.form['prn']

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Fetch order details
    cur.execute("SELECT ORDER_ID, TOTAL_AMOUNT FROM ORDER_TABLE WHERE PRN = %s AND STATUS = FALSE", (prn,))
    order = cur.fetchone()
    if not order:
        return jsonify({"error": "No active order found"}), 404

    # Deduct amount from student's wallet
    cur.execute("SELECT WALLET_BALANCE FROM STUDENT WHERE PRN = %s", (prn,))
    student = cur.fetchone()
    if student['WALLET_BALANCE'] < order['TOTAL_AMOUNT']:
        return jsonify({"error": "Insufficient wallet balance"}), 400

    cur.execute("""
        UPDATE STUDENT
        SET WALLET_BALANCE = WALLET_BALANCE - %s
        WHERE PRN = %s
    """, (order['TOTAL_AMOUNT'], prn))

    # Mark payment as completed
    cur.execute("""
        UPDATE ORDER_TABLE
        SET PAYMENT_STATUS = TRUE
        WHERE ORDER_ID = %s
    """, (order['ORDER_ID'],))

    db.commit()
    return render_template('success.html', message="Order confirmed and payment processed successfully!")

@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    order_id = request.form['order_id']
    status = request.form['status']  # TRUE for completed, FALSE for pending

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE ORDER_TABLE
        SET STATUS = %s
        WHERE ORDER_ID = %s
    """, (status, order_id))

    db.commit()
    return jsonify({"message": "Order status updated"})

@app.route('/')
def home():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM menu_items")
    data = cur.fetchall()
    print(data)  # Debug: Log the data being passed to the template
    categories = {"Fast Food": [],
                  "Nasta": [],
                  "Lunch": [],
                  "Beverages": []}
    for item in data:
        categories[item["CATEGORY"]].append(item)

    return render_template('home.html', data=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        PRN = request.form['PRN']
        password = request.form['password']
        
     
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT * FROM student WHERE PRN = %s', (PRN,))
        user = cur.fetchone()
        cur.close()
        if user and user[6]==password:
            session['PRN'] = user[0]
            session['name'] = user[1]
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/canteen')
def canteen():
    today_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')

    ongoing_orders = fetch_ongoing_orders()
    completed_orders = fetch_completed_orders()

    print(ongoing_orders)   #Debug: Log the fetched orders
    print(completed_orders)  # Debug: Log the fetched orders
    
    return render_template('canteen.html', 
                           today_date=today_date, 
                           current_time=current_time,
                           ongoing_orders=ongoing_orders,
                           completed_orders=completed_orders)

# Function to fetch ongoing orders (from MySQL to DataFrame to Dictionary)
def fetch_ongoing_orders():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM order_table WHERE payment_status = 0 OR status = 0")
    result = cursor.fetchall()
    df = pd.DataFrame(result)
    orders_dict = df.to_dict(orient='records')
    cursor.close()
    connection.close()
    return orders_dict

# Fetch completed orders
def fetch_completed_orders():
    connection = get_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM order_table WHERE payment_status = 1 AND status = 1")
    result = cursor.fetchall()
    df = pd.DataFrame(result)
    orders_dict = df.to_dict(orient='records')
    cursor.close()
    connection.close()
    return orders_dict


if __name__ == "__main__":
    app.run(debug=True)