from flask import Flask, render_template, request,flash, redirect,url_for, session
from flask_mysqldb import MySQL
import re
import datetime
import MySQLdb.cursors

app = Flask(__name__)

# MySQL Configuration
app.secret_key='abcdefg'

app.config['MYSQL_HOST'] = 'localhost'  # Update with your MySQL host
app.config['MYSQL_USER'] = 'root'       # Update with your MySQL username
app.config['MYSQL_PASSWORD'] = ''  # Update with your MySQL password
app.config['MYSQL_DB'] = 'mydatabase'   # Update with your MySQL database name

mysql = MySQL(app)


# Registration Route
@app.route('/register', methods=['GET','POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'phone_number' in request.form and 'password' in request.form and 'department' in request.form and 'vehicle_type' in request.form and 'vehicle_number' in request.form :
        # Get form data
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        department = request.form['department']
        user_type = request.form['user_type']
        vehicle_type = request.form['vehicle_type']
        vehicle_number = request.form['vehicle_number']

        # Create cursor
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE vehicle_number =% s',(vehicle_number,))
        account = cursor.fetchone()
        if account:
            mesage = 'Account Already Exist'
        elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$',email):
            mesage='Invalid email'
        elif not re.match(r'^[A-Za-z]{2}\d{2}[A-Za-z]{2}\d{4}$',vehicle_number):
            mesage= 'Invalid vehicle number'    
        elif not vehicle_number or not password or not email:
            mesage = 'please fill out the form'    
        else:
                if user_type=="admin":
                  cursor.execute("INSERT INTO admin(name, email, phone_number, password, department, user_type,vehicle_type,vehicle_number) VALUES( %s,%s, %s, %s, %s, %s, %s,%s)", (name, email, phone_number, password, department,user_type, vehicle_type,vehicle_number))
                else:      
        # Execute query
                 cursor.execute("INSERT INTO users(name, email, phone_number, password, department, user_type,vehicle_type,vehicle_number) VALUES( %s,%s, %s, %s, %s, %s, %s,%s)", (name, email, phone_number, password, department,user_type, vehicle_type,vehicle_number))
        # Commit to database
                mesage = 'you have successfully registered'
                mysql.connection.commit()
                return render_template('login.html')
       
    elif request.method == 'POST': 
        mesage = 'please fill out the form'  
    return render_template('register.html',mesage=mesage)


# Login Route
@app.route('/')
@app.route('/login', methods=['GET','POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form :
        #and 'vehicle_number' in request.form and 'TotalAmt' in request.form :
        # Get form data
        email = request.form['email']
        password = request.form['password']
        # Create cursor
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Execute query
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password,))
       # cursor.execute ("SELECT vehicle_number,date, TotalAmt FROM log_table WHERE vehicle_number = %s,%s",(vehicle_number,TotalAmt,))
        #results = cursor.fetchall()
        
        # Fetch user
        user = cursor.fetchall()
        print(user)
        if user:
            # User found, redirect to admin page
            session['loggedin'] = True
            session['email'] = email
            mesage='Logged in successfully'

            return redirect('/user')
        
        else:
            # Invalid credentials, show error message
            mesage = 'Invalid email or password'
    return render_template('login.html',mesage=mesage)



#
# user route
@app.route('/user')
def user():
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (session['email'],))
        user = cursor.fetchone()  # Fetch user details

        if user:
            cursor.execute("SELECT entry_date, exit_date, vehicle_type,deductions FROM log_table WHERE vehicle_number = %s", (user['vehicle_number'],))
            user_logs = cursor.fetchall()

            return render_template('user.html', users=[user], user_logs=user_logs)
        else:
            flash("User not found.", 'danger')
            return redirect(url_for('login'))
    # User is not logged in, redirect to the login page
    return redirect(url_for('login'))













@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        if 'loggedin' in session and 'email' in session and 'amount' in request.form:
            email = session['email']
            amount = float(request.form['amount'])  # Convert to float
            method = request.form['payment_method']
            upi_id = request.form['upi_id']
            date = datetime.datetime.now()

            # Update transactions table
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO transactions (user_email, date, amount, method, upi_id) VALUES (%s, %s, %s, %s, %s)",
               (email, date, amount, method, upi_id))
            mysql.connection.commit()

            # Update total_amt in users table
            cursor.execute("UPDATE users SET total_amt = total_amt + %s WHERE email = %s", (amount, email))
            mysql.connection.commit()
            cursor.close()

            flash(f"Payment of Rs{amount:.2f} was successful!")
            return redirect('/user')
        else:
            flash("Payment failed. Please try again.")
            return redirect('/payment')
    else:
        return render_template('payment.html')



@app.route('/transactions')
def transactions():
    if 'loggedin' in session:
        email = session['email']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM transactions WHERE user_email = %s", (email,))
        transactions = cursor.fetchall()
        cursor.close()
        return render_template('transactions.html', transactions=transactions)
    else:
        return redirect(url_for('login'))


    


# adminLogin Route
@app.route('/')
@app.route('/admin', methods=['GET','POST'])
def admin():
    mesage = ''
    if request.method == 'POST' and 'admin_id' in request.form and 'password' in request.form :
        #and 'vehicle_number' in request.form and 'TotalAmt' in request.form :
        # Get form data
        admin_id = request.form['admin_id']
        password = request.form['password']
        #vehicle_number = request.form['vehicle_number']
       # TotalAmt=request.form['TotalAmt']
        
        # Create cursor
        cursor = mysql.connection.cursor()
        
        # Execute query
        cursor.execute("SELECT * FROM admin WHERE admin_id = %s AND password = %s", (admin_id, password,))
       # cursor.execute ("SELECT vehicle_number,date, TotalAmt FROM log_table WHERE vehicle_number = %s,%s",(vehicle_number,TotalAmt,))
        #results = cursor.fetchall()
        
        # Fetch user
        Index = cursor.fetchall()
        
        if Index:
            # User found, redirect to admin page
            session['loggedin'] = True
            session['admin_id'] = admin_id
            mesage = 'Logged in successfully'
           
            return redirect('/index')
    
        else:
            # Invalid credentials, show error message
            mesage = 'Invalid email or password'
    return render_template('admin.html',mesage=mesage)


@app.route('/index')
def Index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT  * FROM users")
    users = cur.fetchall()
    cur.close()
    
    return render_template('index2.html', users=users )
  

@app.route('/search', methods=['GET'])
def search_users():
    search_name = request.args.get('search_name', '')
    cur = mysql.connection.cursor()
    
    if search_name:
        cur.execute("SELECT * FROM users WHERE name LIKE %s", (f"%{search_name}%",))
    else:
        cur.execute("SELECT * FROM users")
    
    users = cur.fetchall()
    cur.close()
    return render_template('index2.html', users=users, search_name=search_name)




@app.route('/approve/<int:userid>', methods=['GET'])
def approve(userid):
    # Update the user status to "approved" in the database
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET status = %s WHERE userid = %s", ('ACTIVE', userid))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('Index'))

@app.route('/reject/<int:userid>', methods=['GET'])
def reject(userid):
    # Update the user status to "rejected" in the database
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET status = %s WHERE userid = %s", ('INACTIVE', userid))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('Index'))




@app.route('/insert', methods = ['POST'])
def insert():

    if request.method == "POST":
        flash("Data Inserted Successfully")
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        department = request.form['department']
        user_type = request.form['user_type']
        vehicle_type = request.form['vehicle_type']
        vehicle_number = request.form['vehicle_number']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, phone_number, password, department, user_type,vehicle_type,vehicle_number) VALUES( %s,%s, %s, %s, %s, %s, %s,%s)", (name, email, phone_number, password, department,user_type, vehicle_type,vehicle_number))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('Index'))



@app.route('/deactivate_user/<int:userid>')
def deactivate_user(userid):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET status = 'INACTIVE' WHERE userid = %s", (userid,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('Index'))




@app.route('/update', methods=['POST', 'GET'])
def update():
    if request.method == 'POST':
        # Get the user ID from the form (assuming you have a hidden input field named 'userid')
        userid = request.form['userid']
        
        # Get the current vehicle data
        cur = mysql.connection.cursor()
        cur.execute("SELECT name,vehicle_type, vehicle_number FROM users WHERE userid = %s", (userid,))
        current_vehicle = cur.fetchone()
        
        # Insert the current vehicle data into vehicle_history table
        # Insert the current vehicle data into vehicle_history table
        cur.execute("""
            INSERT INTO vehicle_history (name, vehicle_type, vehicle_number, change_date)
            VALUES (%s, %s, %s, %s)
        """, ( current_vehicle[0],current_vehicle[2], current_vehicle[1], datetime.datetime.now()))

        # Update the user's data in the users table
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
       # password = request.form['password']
        department = request.form['department']
        user_type = request.form['user_type']
        vehicle_type = request.form['vehicle_type']
        vehicle_number = request.form['vehicle_number']
        
        cur.execute("""
            UPDATE users
            SET name=%s, email=%s, phone_number=%s, department=%s, user_type=%s, vehicle_type=%s, vehicle_number=%s
            WHERE userid=%s
        """, (name, email, phone_number, department, user_type, vehicle_type, vehicle_number, userid))
        
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('Index'))
    
    # Fetch the user's data to prepopulate the edit form
    cur = mysql.connection.cursor()
    
    # Get the user ID from the query parameters (assuming you have a parameter named 'userid')
    userid = request.args.get('userid')
    
    cur.execute("SELECT * FROM users WHERE userid = %s", (userid,))
    user = cur.fetchone()
    cur.close()
    
    return render_template('index2.html', user=user)


@app.route('/vehicle_history')
def vehicle_history():
    # Fetch vehicle history data from the database (replace with your actual query)
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT change_date, name, vehicle_type, vehicle_number FROM vehicle_history")
    vehicle_history_data = cursor.fetchall()
    cursor.close()

    return render_template('vehicle_history.html', vehicle_history_data=vehicle_history_data)




#logout Route
@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('userid',None)
    session.pop('email',None) 
    return redirect(url_for('login')) 


    

if __name__ == '__main__':
    app.run(debug=True)
















