from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error, pooling
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ---------- DATABASE CONNECTION ----------
# Create a connection pool
db_config = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv('DB_PASSWORD', 'A@ihb064'),
    "database": "mobile_shop",
    "pool_name": "mypool",
    "pool_size": 5
}

try:
    connection_pool = pooling.MySQLConnectionPool(**db_config)
except Error as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

def get_connection():
    try:
        if connection_pool:
            return connection_pool.get_connection()
        return None
    except Error as e:
        print(f"Error getting connection from pool: {e}")
        return None

def get_cursor():
    """Get a database cursor, creating connection if needed"""
    db = get_connection()
    if db is None:
        return None, None
    return db, db.cursor(dictionary=True)

# ---------- USER SIGNUP ----------
@app.route("/signup", methods=["POST"])
def signup():
    db = None
    cursor = None
    try:
        if not request.json:
            return jsonify({"success": False, "message": "Invalid request"}), 400
        
        data = request.json
        required_fields = ["username", "email", "password"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Username, email, and password are required"}), 400
        
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        
        username = data["username"].strip()
        email = data["email"].strip()
        password = data["password"]
        
        # Check if username already exists
        cursor.execute("SELECT user_id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Username already exists"}), 400
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Email already exists"}), 400
        
        # Hash password and insert new user
        hashed_password = generate_password_hash(password)
        # Default role is customer
        query = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'customer')"
        cursor.execute(query, (username, email, hashed_password))
        db.commit()
        
        # Get the newly created user
        user_id = cursor.lastrowid
        cursor.execute("SELECT user_id, username, email, role FROM users WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
        
        return jsonify({"success": True, "message": "Account created successfully", "user": user}), 201
        
    except Error as e:
        if db:
            db.rollback()
        print(f"Database error: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500
    except Exception as e:
        if db:
            db.rollback()
        print(f"Server error: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- USER LOGIN ----------
@app.route("/login", methods=["POST"])
def login():
    db = None
    cursor = None
    try:
        if not request.json or "username" not in request.json or "password" not in request.json:
            return jsonify({"success": False, "message": "Username and password required"}), 400
        
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        
        data = request.json
        login_identifier = data["username"].strip()
        password = data["password"]
        
        # Try login with username first, then with email
        query = "SELECT * FROM users WHERE username=%s OR email=%s"
        cursor.execute(query, (login_identifier, login_identifier))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            # Don't return the password hash
            user.pop('password', None)
            return jsonify({"success": True, "user": user})
            
        # Fallback for old plain text passwords (temporary, remove in production)
        if user and user['password'] == password:
             # Don't return the password
            user.pop('password', None)
            return jsonify({"success": True, "user": user})

        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- GOOGLE SIGNIN ----------
@app.route("/google-signin", methods=["POST"])
def google_signin():
    # This is a stub implementation. In a real app, you would verify the Google token.
    # For now, we will simulate a successful login if we get a credential.
    db = None
    cursor = None
    try:
        if not request.json or "credential" not in request.json:
            return jsonify({"success": False, "message": "No credential provided"}), 400
        
        credential = request.json["credential"]
        
        # Here you would verify the JWT token 'credential' with Google's public keys
        # For this example, we'll assume it's valid and contains a dummy email
        # In a real app: idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        
        # Dummy data extracted from "token"
        dummy_email = "google_user@example.com"
        dummy_name = "Google User"
        
        db, cursor = get_cursor()
        if db is None:
             return jsonify({"success": False, "message": "Database error"}), 500
             
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (dummy_email,))
        user = cursor.fetchone()
        
        if not user:
            # Create new user
            # Generate a random password for google users (they won't use it anyway)
            random_password = generate_password_hash(os.urandom(16).hex())
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                (dummy_name, dummy_email, random_password, 'customer')
            )
            db.commit()
            user_id = cursor.lastrowid
            cursor.execute("SELECT user_id, username, email, role FROM users WHERE user_id=%s", (user_id,))
            user = cursor.fetchone()
        else:
            user.pop('password', None)
            
        return jsonify({"success": True, "user": user})
        
    except Exception as e:
        print(f"Google Signin Error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- ADD PRODUCT (ADMIN) ----------
@app.route("/add-product", methods=["POST"])
def add_product():
    db = None
    cursor = None
    try:
        if not request.json:
            return jsonify({"message": "Invalid request"}), 400
        
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"message": "Database connection failed"}), 500
        
        data = request.json
        required_fields = ["name", "price", "quantity"]
        if not all(field in data for field in required_fields):
            return jsonify({"message": "Missing required fields"}), 400
        
        query = """
        INSERT INTO products (name, price, quantity, description, image)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["name"],
            data["price"],
            data["quantity"],
            data.get("description", ""),
            data.get("image", "")
        ))
        db.commit()
        return jsonify({"message": "Product added"}), 201
    except Error as e:
        if db:
            db.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- GET ALL PRODUCTS ----------
@app.route("/products", methods=["GET"])
def get_products():
    db = None
    cursor = None
    try:
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"message": "Database connection failed"}), 500
        
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        return jsonify(products), 200
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- ADD TO CART ----------
@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    db = None
    cursor = None
    try:
        if not request.json:
            return jsonify({"message": "Invalid request"}), 400
        
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"message": "Database connection failed"}), 500
        
        data = request.json
        required_fields = ["user_id", "product_id", "quantity"]
        if not all(field in data for field in required_fields):
            return jsonify({"message": "Missing required fields"}), 400
        
        # Check if product exists and has stock
        cursor.execute("SELECT quantity FROM products WHERE product_id=%s", (data["product_id"],))
        product = cursor.fetchone()
        if not product:
            return jsonify({"message": "Product not found"}), 404
        if product["quantity"] < data["quantity"]:
            return jsonify({"message": "Insufficient stock"}), 400
        
        query = """
        INSERT INTO cart (user_id, product_id, quantity)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            data["user_id"],
            data["product_id"],
            data["quantity"]
        ))
        db.commit()
        return jsonify({"message": "Added to cart"}), 201
    except Error as e:
        if db:
            db.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- VIEW CART ----------
@app.route("/cart/<int:user_id>", methods=["GET"])
def view_cart(user_id):
    db = None
    cursor = None
    try:
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"message": "Database connection failed"}), 500
        
        query = """
        SELECT c.cart_id, p.name, p.price, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id=%s
        """
        cursor.execute(query, (user_id,))
        cart_items = cursor.fetchall()
        return jsonify(cart_items), 200
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- REMOVE FROM CART ----------
@app.route("/cart/<int:cart_id>", methods=["DELETE"])
def remove_from_cart(cart_id):
    db = None
    cursor = None
    try:
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"message": "Database connection failed"}), 500
        
        cursor.execute("DELETE FROM cart WHERE cart_id=%s", (cart_id,))
        if cursor.rowcount == 0:
            return jsonify({"message": "Cart item not found"}), 404
        db.commit()
        return jsonify({"message": "Item removed from cart"}), 200
    except Error as e:
        if db:
            db.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- PLACE ORDER ----------
@app.route("/order", methods=["POST"])
def place_order():
    db = None
    cursor = None
    try:
        if not request.json or "user_id" not in request.json:
            return jsonify({"message": "User ID required"}), 400
        
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"message": "Database connection failed"}), 500
        
        data = request.json
        user_id = data["user_id"]

        # calculate total
        cursor.execute("""
            SELECT p.product_id, p.price, c.quantity, p.quantity as stock
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id=%s
        """, (user_id,))
        items = cursor.fetchall()

        if not items or len(items) == 0:
            return jsonify({"message": "Cart is empty"}), 400

        # Check stock availability
        for item in items:
            if item["stock"] < item["quantity"]:
                return jsonify({"message": f"Insufficient stock for product {item['product_id']}"}), 400

        total = sum(item["price"] * item["quantity"] for item in items)

        # Perform transaction (mysql.connector uses autocommit=False by default)
        try:
            # create order
            cursor.execute("""
                INSERT INTO orders (user_id, order_date, total_amount, status)
                VALUES (%s, %s, %s, %s)
            """, (user_id, date.today(), total, "Placed"))
            order_id = cursor.lastrowid

            # insert order items and reduce stock
            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item["product_id"], item["quantity"], item["price"]))

                # reduce stock
                cursor.execute("""
                    UPDATE products
                    SET quantity = quantity - %s
                    WHERE product_id = %s
                """, (item["quantity"], item["product_id"]))

            # clear cart
            cursor.execute("DELETE FROM cart WHERE user_id=%s", (user_id,))
            
            # Commit transaction
            db.commit()
            return jsonify({"message": "Order placed", "order_id": order_id}), 201
            
        except Exception as e:
            if db:
                db.rollback()
            raise e
            
    except Error as e:
        if db:
            db.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- PAYMENT ----------
@app.route("/payment", methods=["POST"])
def payment():
    db = None
    cursor = None
    try:
        if not request.json or "order_id" not in request.json or "method" not in request.json:
            return jsonify({"message": "Order ID and payment method required"}), 400
        
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"message": "Database connection failed"}), 500
        
        data = request.json
        
        # Verify order exists
        cursor.execute("SELECT order_id FROM orders WHERE order_id=%s", (data["order_id"],))
        order = cursor.fetchone()
        if not order:
            return jsonify({"message": "Order not found"}), 404
        
        cursor.execute("""
            INSERT INTO payments (order_id, payment_method, payment_status, payment_date)
            VALUES (%s, %s, %s, %s)
        """, (data["order_id"], data["method"], "Success", date.today()))
        db.commit()
        return jsonify({"message": "Payment successful"}), 201
    except Error as e:
        if db:
            db.rollback()
        print(f"Database error: {e}")
        return jsonify({"message": "Database error"}), 500
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- CONTACT FORM ----------
@app.route("/api/contact", methods=["POST"])
def contact():
    db = None
    cursor = None
    try:
        if not request.json:
            return jsonify({"success": False, "message": "Invalid request"}), 400
        
        data = request.json
        required_fields = ["name", "email", "subject", "message"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        db, cursor = get_cursor()
        if db is None or cursor is None:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        
        name = data["name"].strip()
        email = data["email"].strip()
        subject = data["subject"].strip()
        message = data["message"].strip()
        user_id = data.get("user_id")  # Optional: track logged-in users
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        # Create contact_messages table if it doesn't exist (matches database.sql schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                status ENUM('new', 'read', 'replied', 'archived') DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        """)
        
        # Insert contact message
        query = """
        INSERT INTO contact_messages (user_id, name, email, subject, message)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, name, email, subject, message))
        db.commit()
        
        message_id = cursor.lastrowid
        
        return jsonify({
            "success": True, 
            "message": "Your message has been sent successfully. We'll get back to you soon!",
            "message_id": message_id
        }), 201
        
    except Error as e:
        if db:
            db.rollback()
        print(f"Database error: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500
    except Exception as e:
        if db:
            db.rollback()
        print(f"Server error: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    print("Starting Flask server...")
    print("Server running on http://localhost:5000")
    print("Note: Set DB_PASSWORD environment variable to override default database password")
    app.run(debug=True, host="0.0.0.0", port=5000)



