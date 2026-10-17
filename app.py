import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import hmac, hashlib

app = Flask(__name__)
CORS(app, origins="*")

# Serve homepage
@app.route("/")
def serve_index():
    return send_from_directory(app.root_path, "index.html")

# Database connection
def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

# ================= DB CONNECTION HELPER =================
def get_db():
    conn = mysql.connector.connect(
        host     = "localhost",
        user     = "root",
        password = "12345",
        database = "novalix"
    )
    return conn


# ================= USER SIGNUP =================
@app.route("/signup", methods=["POST"])
def signup():
    data     = request.json
    username = data["username"]
    email    = data.get("email", "")
    password = data["password"]
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"message": "Username already exists"})
        cursor.execute(
            "INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
            (username, email, password)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Signup success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    data     = request.json
    username = data["username"]
    password = data["password"]
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            return jsonify({"status": "success", "message": "Login successful"})
        else:
            return jsonify({"status": "error", "message": "Invalid username or password"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= ADD BOOK =================
@app.route("/add-book", methods=["POST"])
def add_book():
    data        = request.json
    name        = data.get("name", "")
    author      = data.get("author", "")
    price       = data.get("price", 0)
    image       = data.get("image", "")
    category    = data.get("category", "")
    description = data.get("description", "")
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO books (name,author,price,image,category,description) VALUES (%s,%s,%s,%s,%s,%s)",
            (name, author, price, image, category, description)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Book added"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET BOOKS =================
@app.route("/books", methods=["GET"])
def get_books():
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, author, price, image, category, available, description FROM books"
        )
        rows  = cursor.fetchall()
        conn.close()
        books = []
        for row in rows:
            books.append({
                "id":          row[0],
                "name":        row[1],
                "author":      row[2],
                "price":       float(row[3]) if row[3] else 0,
                "image":       row[4],
                "category":    row[5],
                "available":   row[6],
                "description": row[7] if row[7] else ""
            })
        return jsonify(books)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= DELETE BOOK =================
@app.route("/delete-book/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Book deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= UPDATE BOOK =================
@app.route("/update-book/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    data        = request.json
    name        = data.get("name", "")
    author      = data.get("author", "")
    price       = data.get("price", 0)
    image       = data.get("image", "")
    category    = data.get("category", "")
    description = data.get("description", "")
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET name=%s, author=%s, price=%s, image=%s, category=%s, description=%s WHERE id=%s",
            (name, author, price, image, category, description, book_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Book updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= UPDATE AVAILABILITY =================
@app.route("/update-availability/<int:book_id>", methods=["PUT"])
def update_availability(book_id):
    data = request.json
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET available=%s WHERE id=%s",
            (data["available"], book_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Availability updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= CHECKOUT (COD only) =================
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.json
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO checkout (username, customer_name, phone, email, address, items, total, payment_method, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (data["username"], data["customer_name"], data["phone"], data["email"],
             data["address"], data["items"], data["total"], data["payment_method"], "Order Placed")
        )
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        return jsonify({"message": "Checkout successful", "order_id": order_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET ORDER STATUS =================
@app.route("/order-status/<int:order_id>", methods=["GET"])
def order_status(order_id):
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, items, total, payment_method, status, checkout_date FROM checkout WHERE id=%s",
            (order_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify({
                "id":             row[0],
                "items":          row[1],
                "total":          float(row[2]) if row[2] else 0,
                "payment_method": row[3],
                "status":         row[4],
                "checkout_date":  str(row[5])
            })
        else:
            return jsonify({"error": "Order not found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= UPDATE ORDER STATUS (ADMIN) =================
@app.route("/update-status/<int:order_id>", methods=["PUT"])
def update_status(order_id):
    data = request.json
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE checkout SET status=%s WHERE id=%s",
            (data["status"], order_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Status updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET ALL ORDERS =================
@app.route("/all-orders", methods=["GET"])
def all_orders():
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, customer_name, phone, items, total, payment_method, checkout_date, status FROM checkout ORDER BY checkout_date DESC"
        )
        rows   = cursor.fetchall()
        conn.close()
        orders = []
        for row in rows:
            orders.append({
                "id":             row[0],
                "username":       row[1],
                "customer_name":  row[2],
                "phone":          row[3],
                "items":          row[4],
                "total":          float(row[5]) if row[5] else 0,
                "payment_method": row[6],
                "checkout_date":  str(row[7]),
                "status":         row[8]
            })
        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET MY ORDERS =================
@app.route("/my-orders/<username>", methods=["GET"])
def my_orders(username):
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, items, total, payment_method, checkout_date, status, address FROM checkout WHERE username=%s ORDER BY checkout_date DESC",
            (username,)
        )
        rows   = cursor.fetchall()
        conn.close()
        orders = []
        for row in rows:
            orders.append({
                "id":             row[0],
                "items":          row[1],
                "total":          float(row[2]) if row[2] else 0,
                "payment_method": row[3],
                "checkout_date":  str(row[4]),
                "status":         row[5],
                "address":        row[6] or "Address not available"
            })
        return jsonify(orders)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= USER PROFILE =================
@app.route("/user-profile/<username>", methods=["GET"])
def user_profile(username):
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM checkout WHERE username=%s", (username,))
        total_orders = cursor.fetchone()[0]
        conn.close()
        if user:
            return jsonify({
                "username":     user[0],
                "email":        user[1] or "Not provided",
                "total_orders": total_orders
            })
        else:
            return jsonify({"error": "User not found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET ALL USERS =================
@app.route("/all-users", methods=["GET"])
def all_users():
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users")
        rows  = cursor.fetchall()
        conn.close()
        users = []
        for row in rows:
            users.append({
                "id":       row[0],
                "username": row[1],
                "email":    row[2]
            })
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= CHECK USER EXISTS =================
@app.route("/check-user", methods=["POST"])
def check_user():
    data     = request.json
    username = data["username"]
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        conn.close()
        return jsonify({"exists": bool(user)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= RESET PASSWORD =================
@app.route("/reset-password", methods=["POST"])
def reset_password():
    data         = request.json
    username     = data["username"]
    new_password = data["new_password"]
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (new_password, username)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Password reset successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= ADD REVIEW =================
@app.route("/add-review", methods=["POST"])
def add_review():
    data = request.json
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (book_id, username, rating, review) VALUES (%s,%s,%s,%s)",
            (data["book_id"], data["username"], data["rating"], data["review"])
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Review added!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET REVIEWS =================
@app.route("/get-reviews/<int:book_id>", methods=["GET"])
def get_reviews(book_id):
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, rating, review, review_date FROM reviews WHERE book_id=%s ORDER BY review_date DESC",
            (book_id,)
        )
        rows    = cursor.fetchall()
        conn.close()
        reviews = []
        for row in rows:
            reviews.append({
                "username":    row[0],
                "rating":      row[1],
                "review":      row[2],
                "review_date": str(row[3])
            })
        return jsonify(reviews)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= GET AVG RATING =================
@app.route("/avg-rating/<int:book_id>", methods=["GET"])
def avg_rating(book_id):
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE book_id=%s",
            (book_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return jsonify({
            "avg":   round(float(row[0]), 1) if row[0] else 0,
            "count": row[1]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= CANCEL ORDER =================
@app.route("/cancel-order/<int:order_id>", methods=["PUT"])
def cancel_order(order_id):
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status FROM checkout WHERE id=%s", (order_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Order not found"}), 404
        if row[0] != "Order Placed":
            conn.close()
            return jsonify({"error": f"Cannot cancel order in '{row[0]}' stage"}), 400
        cursor.execute(
            "UPDATE checkout SET status=%s WHERE id=%s", ("Cancelled", order_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Order cancelled", "refund_done": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
