from flask import Blueprint, request, session, redirect, url_for, render_template
from models import db, User, Doctor
import bcrypt


auth = Blueprint('auth', __name__)

# Register
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        specialization = request.form.get('specialization')

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('auth.html', error='Email already registered')

        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create user
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role
        )
        db.session.add(new_user)
        db.session.flush()  # Gets the new user ID before committing

        # If doctor, create doctor profile
        if role == 'doctor':
            doctor_profile = Doctor(
                user_id=new_user.id,
                specialization=specialization
            )
            db.session.add(doctor_profile)

        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('auth.html')


# Login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return render_template('auth.html', error='Invalid email or password')

        # Save user info to session
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['role'] = user.role

        # Redirect based on role
        if user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        else:
            return redirect(url_for('patient.dashboard'))

    return render_template('auth.html')


# Logout
@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))