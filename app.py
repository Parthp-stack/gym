from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '@Rupali231985'
app.config['MYSQL_DB'] = 'gym_db'

mysql = MySQL(app)

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        print("Login attempt: ", username, password, role)

        cur = mysql.connection.cursor()

        if role == 'admin':
            cur.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
            user = cur.fetchone()
            print("Admin found:", user)
            if user:
                session['admin_id'] = user[0]
                session['username'] = user[1]
                session['role'] = 'admin'
                return redirect('/admin_dashboard')
            else:
                flash("Invalid admin credentials", "danger")
                return redirect('/login')

        elif role == 'client':
            cur.execute("SELECT * FROM clients WHERE username = %s AND password = %s", (username, password))
            user = cur.fetchone()
            print("Client found:", user)
            if user:
                session['client_id'] = user[0]
                session['username'] = user[1]
                session['role'] = 'client'
                return redirect('/client_dashboard')
            else:
                flash("Invalid client credentials", "danger")
                return redirect('/login')

        flash("Role not selected properly", "danger")
        return redirect('/login')

    return render_template('login.html')

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE username = %s", (username,))
        existing = cur.fetchone()
        if existing:
            flash("Username already exists.", "danger")
            return redirect('/admin_register')

        cur.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()
        flash("Admin registered successfully!", "success")
        return redirect('/login')

    return render_template('admin_register.html')

@app.route('/client_register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Save to DB
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO clients (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cursor.close()

        flash("Client registered successfully!", "success")
        return redirect('/login')
    
    return render_template('register.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only.", "warning")
        return redirect('/login')

    cur = mysql.connection.cursor()

    # ✅ Get all clients
    # Inside your admin route
    cur.execute("SELECT id, username, country, join_date FROM clients")
    clients = cur.fetchall()


    # ✅ Total number of users
    # total_users = len(clients)
    cur.execute("SELECT COUNT(*) FROM clients")
    total_users = cur.fetchone()[0]

    # ✅ Total amount of money collected
    cur.execute("SELECT SUM(amount) FROM payments")
    total_amount = cur.fetchone()[0]
    total_amount = total_amount if total_amount else 0

    cur.close()

    return render_template('admin_dashboard.html',
                           clients=clients,
                           total_users=total_users,
                           total_amount=total_amount,
                           username=session['username'])

@app.route('/client_dashboard')
def client_dashboard():
    if 'client_id' not in session:
        return redirect('/login')

    client_id = session['client_id']
    cursor = mysql.connection.cursor()

    # Get username and join date
    cursor.execute("SELECT username, join_date FROM clients WHERE id = %s", (client_id,))
    user = cursor.fetchone()

    if not user:
        flash("Client not found.")
        return redirect('/login')

    # Get payments
    cursor.execute("SELECT amount, date_paid FROM payments WHERE client_id = %s ORDER BY date_paid DESC", (client_id,))
    payments = cursor.fetchall()

    # Get motivation (latest message or default)
    cursor.execute("SELECT message FROM motivations WHERE client_id = %s ORDER BY date_added DESC LIMIT 1", (client_id,))
    result = cursor.fetchone()
    motivation = result if result else ("Stay strong and keep going!",)


    # Get menus
    cursor.execute("SELECT content, type FROM menus WHERE client_id = %s", (client_id,))
    menus = cursor.fetchall()

    cursor.close()

    return render_template("client_dashboard.html",
                           username=user[0],
                           join_date=user[1],
                           payments=payments,
                           motivation=motivation,
                           menus=menus)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        country= request.form['country']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO clients (username, password,country, join_date) VALUES (%s, %s, %s)", 
                    (username, password,country, datetime.now()))
        mysql.connection.commit()
        cur.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    username = session['username']
    role = session['role']

    cur = mysql.connection.cursor()
    if role == 'client':
        cur.execute("SELECT id,country, join_date FROM clients WHERE username = %s", (username,))
        client = cur.fetchone()
        # cur.execute("SELECT amount, date_paid FROM payments WHERE client_id = %s", (client[0],))
        cur.execute("SELECT amount, date_paid FROM payments WHERE client_id = %s ORDER BY date_paid DESC", (client[0],))
        # cur.execute("SELECT amount, date_paid FROM payments WHERE client_id = %s ORDER BY date_paid DESC", (client[0],))
        payments = cur.fetchall()
        cur.execute("SELECT message FROM motivations WHERE client_id = %s ORDER BY date_added DESC LIMIT 1", (client[0],))
        motivation = cur.fetchone()
        cur.execute("SELECT content, type FROM menus WHERE client_id = %s", (client[0],))
        menus = cur.fetchall()
        cur.close()
        return render_template('client_dashboard.html', username=username, join_date=client[1],
                               payments=payments, motivation=motivation, menus=menus)
    else:
        cur.execute("SELECT * FROM clients")
        clients = cur.fetchall()
        cur.close()
        return render_template('admin_dashboard.html', clients=clients)

from datetime import datetime

@app.route('/add_payment', methods=['POST'])
def add_payment():
    if 'username' not in session or session['role'] != 'admin':
        return redirect('/login')

    username = request.form['username']
    amount = request.form['amount']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM clients WHERE username = %s", (username,))
    client = cur.fetchone()

    if client:
        client_id = client[0]
        cur.execute("INSERT INTO payments (client_id, amount, date_paid) VALUES (%s, %s, %s)",
                    (client_id, amount, datetime.now()))
        mysql.connection.commit()
        flash('Payment added successfully!', 'success')
    else:
        flash('Client not found!', 'danger')

    cur.close()
    return redirect('/admin_dashboard')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
