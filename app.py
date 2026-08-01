import sqlite3
from flask import Flask, render_template, request,redirect,url_for,session
from werkzeug.security import check_password_hash,generate_password_hash
app = Flask(__name__)

app.secret_key = "resconnect_secret_key"

# ----------------------------
# Create Database and Tables
# ----------------------------

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

print("Database Connected")

# Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    mobile TEXT,
    mobile2 TEXT,
    password TEXT
)
""")

# Admins Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_name TEXT,
    email TEXT,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS help_requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    status TEXT,
    claimed_by INTEGER,
    created_at TEXT)""")

connection.commit()
connection.close()


# ----------------------------
# Insert Default Admin (Run Once)
# ----------------------------

#deleted the code as wanted to insert only the admin once for training

# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/claim/<int:request_id>", methods=["POST"])
def claim(request_id):
    admin_id = session["admin_id"]

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE help_requests
    SET status = ?, claimed_by = ?
    WHERE id = ?
    """, ("Claimed", admin_id, request_id))

    connection.commit()
    connection.close()

    return redirect(url_for("admin_dashboard"))
    

@app.route("/admin_dashboard")
def admin_dashboard():

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""SELECT
users.name,
users.mobile,
users.mobile2,
help_requests.id,
help_requests.category,
help_requests.status,
help_requests.claimed_by,
admins.ngo_name

FROM help_requests

JOIN users
ON help_requests.user_id = users.id

LEFT JOIN admins
ON help_requests.claimed_by = admins.id"""

)
    requests = cursor.fetchall()

    return render_template(
    "admin dashboard.html",
     requests=requests,   #invalid without comma 
     admin_id=session["admin_id"]
)

#we have created these routes to use redirect method url for so that we can claim its function as now we dont want to
#use render template
@app.route("/user_dashboard")
def user_dashboard():
    user_id = session["user_id"]
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.execute("""SELECT
help_requests.category,
help_requests.status,
admins.ngo_name

FROM help_requests

LEFT JOIN admins
ON help_requests.claimed_by = admins.id        

WHERE help_requests.user_id = ?
                 """, (user_id,))
    user_requests = cursor.fetchall()

    return render_template("user dashboard.html",
  user_requests=user_requests)




@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login_page"))



@app.route("/login" , methods=["GET","POST"])
def login_page():
    if request.method == "GET":
        return render_template("admin page.html")

    # POST starts here

    email = request.form["email"]
    password = request.form["password"]


    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM admins
    WHERE email=? AND password=?
    """, (email, password))

    admin=cursor.fetchone()  #matches 1st row with admin table

    if admin:
        session["role"] = "admin"
        session["admin_id"] = admin[0]
        connection.close()
        return redirect(url_for("admin_dashboard"))
    
    connection.close()

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM users
    WHERE email=? 
    """, (email,))
    # we remove password as hashed now

    user=cursor.fetchone()  

    if user and check_password_hash(user[5], password):
        session["role"] = "user"
        session["user_id"] = user[0]
        return redirect(url_for("user_dashboard"))
    connection.close()

    connection.close()
    return "invalid details"

    



@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "GET":
       return render_template("user page.html")
    #post start here
    name = request.form["name"]
    email = request.form["email"]
    mobile = request.form["mobile"]
    mobile2 = request.form["mobile2"]
    password = request.form["password"]


    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.execute("""
    SELECT * FROM users
    WHERE email=?
    """, (email,))
    
    existing_user = cursor.fetchone()



    if existing_user:
     connection.close()
     return "Email already registered"
    
    password = generate_password_hash(password)

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
    INSERT INTO users(name,email,mobile,mobile2,password)
    VALUES(?,?,?,?,?)
    """, (name, email, mobile, mobile2, password))

    connection.commit()
    connection.close()

    return redirect(url_for("login_page"))

# NOW WE WILL CRETE THE ROUTE FOR THE GATHERING OF THE REQUEST OF HELP 

@app.route("/request_help", methods=["GET", "POST"])
def request_help():

    if request.method == "GET":
        return redirect(url_for("user_dashboard"))

    # POST starts here

    user_id = session["user_id"]
    category = request.form["category"]

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    
    cursor.execute("""
    SELECT *
    FROM help_requests
    WHERE user_id=? AND category=? AND status IN ('Pending','Claimed')
    """, (user_id, category))
    
    existing_request = cursor.fetchone()
    if existing_request:
        connection.close()
        return "You already have an active request."

    cursor.execute("""
    INSERT INTO help_requests(user_id, category, status, claimed_by, created_at)
    VALUES(?, ?, ?, ?, datetime('now'))
    """, (user_id, category, "Pending", None))

    connection.commit()
    connection.close()

    return redirect(url_for("user_dashboard"))


#yha pe url_for jo h na woh login page mtlb function jo rkha h uska naam leta  h


import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
