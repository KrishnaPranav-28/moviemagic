from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import uuid
import os

app = Flask(__name__)
app.secret_key = 'your_static_secret_key_here'  # Replace with your own secret string

# SQLite Database Configuration
DATABASE = 'movie_magic.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        # Create users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        # Create bookings table
        db.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id TEXT PRIMARY KEY,
                movie_name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                theater TEXT NOT NULL,
                address TEXT NOT NULL,
                booked_by TEXT NOT NULL,
                user_name TEXT NOT NULL,
                seats TEXT NOT NULL,
                amount_paid TEXT NOT NULL,
                booking_time TEXT NOT NULL,
                FOREIGN KEY (booked_by) REFERENCES users (email)
            )
        ''')
        db.commit()
        db.close()

# Initialize the database
init_db()

# Authentication Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            db.close()
            
            if user and check_password_hash(user['password'], password):
                session['user'] = {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email']
                }
                return redirect(url_for('home1'))
            
            flash('Invalid email or password', 'danger')
        except Exception as e:
            print(f"Database error: {str(e)}")
            flash('An error occurred. Please try again later.', 'danger')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        try:
            db = get_db()
            # Check if user already exists
            existing_user = db.execute('SELECT email FROM users WHERE email = ?', (email,)).fetchone()
            if existing_user:
                flash('Email already registered!', 'danger')
                return redirect(url_for('signup'))
            
            # Create new user
            user_id = str(uuid.uuid4())
            db.execute(
                'INSERT INTO users (id, name, email, password, created_at) VALUES (?, ?, ?, ?, ?)',
                (user_id, name, email, password, datetime.now().isoformat())
            )
            db.commit()
            db.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Database error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
            
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))

# Application Routes
@app.route('/home1')
def home1():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home1.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact_us')
def contact():
    return render_template('contact_us.html')

@app.route('/b1', methods=['GET'], endpoint='b1')
def booking_page():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('b1.html',
        movie=request.args.get('movie'),
        theater=request.args.get('theater'),
        address=request.args.get('address'),
        price=request.args.get('price')
    )

@app.route('/tickets', methods=['POST'])
def tickets():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    try:
        # Extract booking details from form
        movie_name = request.form.get('movie')
        booking_date = request.form.get('date')  
        show_time = request.form.get('time')
        theater_name = request.form.get('theater')
        theater_address = request.form.get('address')
        selected_seats = request.form.get('seats')
        amount_paid = request.form.get('amount')
        
        # Generate a unique booking ID
        booking_id = f"MVM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Store booking in database
        db = get_db()
        db.execute(
            '''INSERT INTO bookings 
            (booking_id, movie_name, date, time, theater, address, booked_by, user_name, seats, amount_paid, booking_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (booking_id, movie_name, booking_date, show_time, theater_name, theater_address, 
             session['user']['email'], session['user']['name'], selected_seats, amount_paid, 
             datetime.now().isoformat())
        )
        db.commit()
        db.close()
        
        # Simulate sending email notification
        send_booking_confirmation({
            'booking_id': booking_id,
            'movie_name': movie_name,
            'date': booking_date,
            'time': show_time,
            'theater': theater_name,
            'address': theater_address,
            'user_name': session['user']['name'],
            'seats': selected_seats,
            'amount_paid': amount_paid,
            'booked_by': session['user']['email']
        })
        
        flash('Booking successful! Confirmation has been sent to your email.', 'success')
        
        # Get the booking details to display
        booking_item = {
            'booking_id': booking_id,
            'movie_name': movie_name,
            'date': booking_date,
            'time': show_time,
            'theater': theater_name,
            'address': theater_address,
            'seats': selected_seats,
            'amount_paid': amount_paid
        }
        
        return render_template('tickets.html', booking=booking_item)
        
    except Exception as e:
        print(f"Error processing booking: {str(e)}")
        flash('Error processing booking', 'danger')
        return redirect(url_for('home1'))

def send_booking_confirmation(booking):
    """Simulate sending booking confirmation email"""
    try:
        print(f"\n=== Booking Confirmation Email ===\n"
              f"To: {booking['booked_by']}\n"
              f"Subject: MovieMagic Booking Confirmation - {booking['booking_id']}\n\n"
              f"Hello {booking['user_name']},\n\n"
              f"Your movie ticket booking is confirmed!\n\n"
              f"Booking Details:\n"
              f"----------------\n"
              f"Booking ID: {booking['booking_id']}\n"
              f"Movie: {booking['movie_name']}\n"
              f"Date: {booking['date']}\n"
              f"Time: {booking['time']}\n"
              f"Theater: {booking['theater']}\n"
              f"Location: {booking['address']}\n"
              f"Seats: {booking['seats']}\n"
              f"Amount Paid: ₹{booking['amount_paid']}\n\n"
              f"Please show this confirmation at the theater to collect your tickets.\n\n"
              f"Thank you for choosing MovieMagic!\n")
        return True
    except Exception as e:
        print(f"Error sending booking confirmation: {str(e)}")
        return False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)