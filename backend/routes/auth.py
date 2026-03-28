from flask import Blueprint, request, session, redirect, url_for, render_template, flash
import bcrypt
from models import db, User, Doctor

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form['role']
        specialization = request.form.get('specialization', '').strip()

        # Validation
        if not name or len(name) < 2:
            flash('Name must be at least 2 characters.', 'error')
            return render_template('auth.html')

        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return render_template('auth.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth.html')

        if role == 'doctor' and not specialization:
            flash('Please enter your specialization.', 'error')
            return render_template('auth.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('auth.html')

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(name=name, email=email, password_hash=password_hash, role=role)
        db.session.add(new_user)
        db.session.flush()

        if role == 'doctor':
            doctor_profile = Doctor(user_id=new_user.id, specialization=specialization)
            db.session.add(doctor_profile)

        db.session.commit()
        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # Validation
        if not email or '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return render_template('auth.html')

        if not password:
            flash('Please enter your password.', 'error')
            return render_template('auth.html')

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            flash('Invalid email or password.', 'error')
            return render_template('auth.html')

        session['user_id'] = user.id
        session['user_name'] = user.name
        session['role'] = user.role

        if user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        else:
            return redirect(url_for('patient.dashboard'))

    return render_template('auth.html')


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))