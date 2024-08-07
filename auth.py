from datetime import date
import logging
from flask import Flask, jsonify, request
import sqlite3
import random
import string

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)


# Hardcoded valid credentials for the login endpoint
valid_email = 'skbd@skbd.com'
valid_password = 'skbd0001'

# Function to verify API key


def verify_key(key):
    with sqlite3.connect('login_notification_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM login_key WHERE key=?', (key,))
        return cursor.fetchone() is not None


# Function to create SQLite database and tables if they don't exist


def create_database_and_tables():
    with sqlite3.connect('inventory.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT,
                quantity INTEGER,
                batch_no TEXT,
                manufacture_date TEXT,
                expiry_date TEXT,
                dealer_name TEXT,
                price INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT,
                quantity INTEGER,
                batch_no TEXT,
                manufacture_date TEXT,
                expiry_date TEXT,
                dealer_name TEXT,
                price INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dealers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                address TEXT,
                phone_no TEXT,
                email TEXT,
                panno NUMBER,
                dd_reg TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone_no TEXT,
                address TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                customer_id INTEGER,
                quantity INTEGER,
                total_price REAL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES items(id),
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        ''')
        conn.commit()
    logging.info("SQLite database 'inventory.db' and all tables created.")

    with sqlite3.connect('login_notification_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_key (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user TEXT,
                       login_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       key TEXT
                       )''')

        cursor.execute('''
     CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    body TEXT,
    title TEXT,
    key TEXT,
    status INTEGER,
    FOREIGN KEY(key) REFERENCES login_key(key)
)
''')
        conn.commit()


# Call the function to create the database and tables
create_database_and_tables()


def gen_key():
    N = 7
    res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
    return res


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not all(key in data for key in ['email', 'password', 'app']):
        return jsonify({'message': 'email, password, and app are required'}), 400

    if data['email'] != valid_email or data['password'] != valid_password or data['app'] != 'svp_admin':
        return jsonify({'message': 'Invalid email or password'}), 401

    key = str(gen_key())
    with sqlite3.connect('login_notification_data.db') as conn:
        cursor = conn.cursor()

        # Ensure the key is unique
        cursor.execute('SELECT 1 FROM login_key WHERE key = ?', (key,))
        while cursor.fetchone() is not None:
            key = str(gen_key())
            cursor.execute('SELECT 1 FROM login_key WHERE key = ?', (key,))

        cursor.execute(
            'INSERT INTO login_key(user, key) VALUES (?, ?)', (valid_email, key))
        conn.commit()

    return jsonify({'message': 'Login successful', 'key': key}), 200


@app.route('/add-item', methods=['POST'])
def add_item():
    data = request.get_json()
    required_fields = ['item', 'quantity', 'batchNo',
                       'manufactureDate', 'expiryDate', 'dealerName', 'price', 'key']

    if not all(field in data for field in required_fields):
        missing_fields = [
            field for field in required_fields if field not in data]
        return jsonify({'message': f'Missing fields: {", ".join(missing_fields)}'}), 400

    # Authenticator
    key = data['key']
    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401

    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (item, quantity, batch_no, manufacture_date, expiry_date, dealer_name, price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data['item'], data['quantity'], data['batchNo'], data['manufactureDate'], data['expiryDate'], data['dealerName'], data['price']))
            cursor.execute('''
                INSERT INTO items_data (item, quantity, batch_no, manufacture_date, expiry_date, dealer_name, price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data['item'], data['quantity'], data['batchNo'], data['manufactureDate'], data['expiryDate'], data['dealerName'], data['price']))
            conn.commit()
        return jsonify({'message': 'Item added successfully', 'data': data}), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to add item'}), 500


@app.route('/dealers', methods=['GET'])
def get_dealers():
    # Authenticator
    key = request.args.get('key')
    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401
    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM dealers")
            dealers = cursor.fetchall()
        dealer_names = [dealer[0] for dealer in dealers]
        return jsonify(dealer_names), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to fetch dealer names'}), 500


@app.route('/customers', methods=['GET'])
def get_customers():

    # Authenticator
    key = request.args.get('key')
    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401
    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM customers")
            customers = cursor.fetchall()
        customer_names = [customer[0] for customer in customers]
        return jsonify(customer_names), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to fetch customer names'}), 500


@app.route('/add-dealer', methods=['POST'])
def add_dealer():
    data = request.get_json()
    required_fields = ['name', 'address',
                       'phoneNo', 'email', 'panno', 'dd_reg', 'key']
    if not all(field in data for field in required_fields):
        missing_fields = [
            field for field in required_fields if field not in data]
        return jsonify({'message': f'Missing fields: {", ".join(missing_fields)}'}), 400

     # Authenticator
    key = data['key']
    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401
    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dealers (name, address, phone_no, email, panno, dd_reg)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['name'], data['address'], data['phoneNo'], data['email'], data['panno'], data['dd_reg']))
            conn.commit()
        return jsonify({'message': 'Dealer added successfully', 'data': data}), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to add dealer'}), 500


@app.route('/products', methods=['GET'])
def get_products():
    # Authenticator
    key = request.args.get('key')
    if not verify_key(key):
        print("Not authenticated")
        return jsonify({'message': 'Not Authenticated'}), 401

    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, item, manufacture_date, expiry_date, batch_no, price, quantity
                FROM items
            ''')
            items = cursor.fetchall()

        products = [{'id': item[0], 'name': item[1], 'manufacture_date': item[2], 'expiry_date': item[3],
                     'batch_no': item[4], 'price': item[5], 'quantity': item[6]} for item in items]
        return jsonify(products), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to fetch products'}), 500


@app.route('/sell', methods=['POST'])
def sell_product():
    data = request.get_json()
    required_fields = ['productIds', 'batchNo', 'quantity',
                       'total_price', 'customerName', 'phoneNo', 'address', 'key']
    if not all(field in data for field in required_fields):
        missing_fields = [
            field for field in required_fields if field not in data]
        return jsonify({'message': f'Missing fields: {", ".join(missing_fields)}'}), 400

    product_ids = data['productIds']
    batch_nos = data['batchNo']
    quantity = data['quantity']
    total_price = data['total_price']
    # Authenticator
    key = data['key']
    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401

    if not isinstance(product_ids, list) or not isinstance(batch_nos, list) or len(product_ids) != len(batch_nos):
        return jsonify({'message': 'productIds and batchNo must be lists of the same length'}), 400
    if not isinstance(quantity, int):
        return jsonify({'message': 'quantity must be an integer'}), 400
    if not isinstance(total_price, (int, float)):
        return jsonify({'message': 'total_price must be a number'}), 400

    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO customers (name, phone_no, address)
                VALUES (?, ?, ?)
            ''', (data['customerName'], data['phoneNo'], data['address']))
            customer_id = cursor.lastrowid

            for product_id, batch_no in zip(product_ids, batch_nos):
                if not check_quantity(cursor, product_id, batch_no, quantity):
                    conn.rollback()
                    return jsonify({'message': f'Not enough quantity for product ID {product_id} and batch no {batch_no}'}), 400

                cursor.execute('''
                    INSERT INTO sales (product_id, customer_id, quantity, total_price)
                    VALUES (?, ?, ?, ?)
                ''', (product_id, customer_id, quantity, total_price))

                cursor.execute('''
                    UPDATE items
                    SET quantity = quantity - ?
                    WHERE id = ? AND batch_no = ?
                ''', (quantity, product_id, batch_no))

            conn.commit()
        return jsonify({'message': 'Product(s) sold successfully'}), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to sell product'}), 500


def check_quantity(cursor, product_id, batch_no, quantity):
    cursor.execute(
        'SELECT quantity FROM items WHERE id = ? AND batch_no = ?', (product_id, batch_no))
    item = cursor.fetchone()
    if item is None or item[0] < quantity:
        return False
    return True


@app.route('/daily-report', methods=['GET'])
def daily_report():
    report_date = request.args.get('date', date.today().isoformat())
    dealer_name = request.args.get('dealer_name')
    customer_name = request.args.get('customer_name')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    key = request.args.get('key')

    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401

    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()

            query = '''
                SELECT 'Added' AS type, item, quantity, batch_no, manufacture_date AS date, dealer_name, added_date, NULL AS customer_name, NULL AS total_price
                FROM items
                WHERE date(added_date) = ?
            '''
            params = [report_date]

            if dealer_name:
                query += ' AND dealer_name = ?'
                params.append(dealer_name)

            if start_date and end_date:
                query += ' AND date(added_date) BETWEEN ? AND ?'
                params.extend([start_date, end_date])

            query += '''
                UNION ALL

                SELECT 'Sold' AS type, i.item, s.quantity, i.batch_no, i.manufacture_date AS date, NULL AS dealer_name, s.sale_date AS added_date, c.name as customer_name, s.total_price
                FROM sales s
                JOIN items i ON s.product_id = i.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE date(s.sale_date) = ?
            '''
            params.append(report_date)

            if customer_name:
                query += ' AND c.name = ?'
                params.append(customer_name)

            if start_date and end_date:
                query += ' AND date(s.sale_date) BETWEEN ? AND ?'
                params.extend([start_date, end_date])

            cursor.execute(query, params)
            products = cursor.fetchall()

        added_products = []
        sold_products = []
        for product in products:
            product_data = {
                'item': product[1],
                'quantity': product[2],
                'batch_no': product[3],
                'date': product[4],
                'dealer_name': product[5],
                'added_date': product[6],
                'customer_name': product[7],
                'total_price': product[8]
            }
            if product[0] == 'Added':
                added_products.append(product_data)
            else:
                sold_products.append(product_data)

        report = {
            'date': report_date,
            'added_products': added_products,
            'sold_products': sold_products
        }

        return jsonify(report), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to generate daily report'}), 500
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'message': 'Failed to load daily report'}), 500


@app.route('/clear-data', methods=['POST'])
def clear_data():
    data = request.get_json()
    clear_items = data.get('clear_items', False)
    clear_sales = data.get('clear_sales', False)
    clear_customers = data.get('clear_customers', False)
    clear_dealers = data.get('clear_dealers', False)
    key = data.get('key')

    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401
    try:
        with sqlite3.connect('inventory.db') as conn:
            cursor = conn.cursor()
            if clear_items:
                cursor.execute("DELETE FROM items")
            if clear_sales:
                cursor.execute("DELETE FROM sales")
            if clear_customers:
                cursor.execute("DELETE FROM customers")
            if clear_dealers:
                cursor.execute("DELETE FROM dealers")
            conn.commit()

        return jsonify({'message': 'Data cleared successfully'}), 200

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        return jsonify({'message': 'Failed to clear data'}), 500


@app.route('/version-manager', methods=['POST'])
def version():
    data = request.get_json()
 # List of required fields
    required_fields = ['version']

    # Check if all required fields are in the incoming data
    if not all(field in data for field in required_fields):
        missing_fields = [
            field for field in required_fields if field not in data]
        return jsonify({'message': f'Missing fields: {", ".join(missing_fields)}'}), 400

    # reads the url file for the latest url
    with open('url', 'r') as file:
        content = file.read()

    with open('version', 'r') as file2:
        ver = file2.read()
    print(ver)
    print(content)
    # Latest version
    global_version = f'v{ver}'
    new_version_url = content.strip()
    new_version_url = new_version_url+'/app-release.apk'

    client_version = data['version']

    # Check if client version matches the global version
    if client_version != global_version:
        print('update_needed')
        return jsonify({
            'status': 'update_needed',
            'global_version': global_version,
            'url': new_version_url,
            'message': f'New version available: {global_version}'
        }), 200

    # If versions match, return a success message
    print('up_to_date')
    return jsonify({'status': 'up_to_date', 'message': 'Version is up to date'}), 200


@app.route('/notice', methods=['POST'])
def notice():
    data = request.get_json()
    # List of required fields
    required_fields = ['key']

    # Check if all required fields are in the incoming data
    if not all(field in data for field in required_fields):
        missing_fields = [
            field for field in required_fields if field not in data]
        return jsonify({'message': f'Missing fields: {", ".join(missing_fields)}'}), 400

    key = data['key']

    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401

    status = 0

    # Fetch the notification
    with sqlite3.connect('login_notification_data.db') as conn2:
        cursor2 = conn2.cursor()
        cursor2.execute(
            'SELECT id,body, title FROM notifications WHERE key=? AND status=?', (key, status))
        dd2 = cursor2.fetchall()

    if not dd2:
        return jsonify({'message': 'No notifications found'}), 404

    id, body, title = dd2[0]

    # Update the notification status
    new_status = 1
    with sqlite3.connect('login_notification_data.db') as conn3:
        cursor3 = conn3.cursor()
        cursor3.execute(
            'UPDATE notifications SET status = ? WHERE key = ? AND id=?', (new_status, key, id))
        conn3.commit()

    return jsonify({'message': 'Authenticated', 'title': title, 'body': body})


@app.route('/notices', methods=['POST'])
def notices():
    data = request.get_json()
    # List of required fields
    required_fields = ['key']

    # Check if all required fields are in the incoming data
    if not all(field in data for field in required_fields):
        missing_fields = [
            field for field in required_fields if field not in data]
        return jsonify({'message': f'Missing fields: {", ".join(missing_fields)}'}), 400

    key = data['key']

    if not verify_key(key):
        return jsonify({'message': 'Not Authenticated'}), 401

    with sqlite3.connect('login_notification_data.db') as conn2:
        cursor2 = conn2.cursor()
        cursor2.execute(
            'SELECT body, title FROM notifications WHERE key=?', (key))
        dd3 = cursor2.fetchall()
        notification = [{'message': 'Authentiated',
                         'title': ntfy[1], 'body': ntfy[0]} for ntfy in dd3]
    return jsonify(notification), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
