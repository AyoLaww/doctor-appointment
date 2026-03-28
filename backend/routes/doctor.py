from flask import Blueprint, render_template, session, redirect, url_for, request
from models import db, Availability, Appointment, User, Doctor
from datetime import datetime

doctor = Blueprint('doctor', __name__)

# Protect route - only doctors can access
def doctor_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'doctor':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# Doctor dashboard
@doctor.route('/doctor/dashboard')
@doctor_required
def dashboard():
    # Get doctor profile
    doctor_profile = Doctor.query.filter_by(user_id=session['user_id']).first()

    # Get availability slots
    availability = Availability.query.filter_by(
        doctor_id=doctor_profile.id
    ).order_by(Availability.date, Availability.start_time).all()

    # Get booked appointments
    appointments = db.session.query(Appointment, Availability, User)\
        .join(Availability, Appointment.availability_id == Availability.id)\
        .join(User, Appointment.patient_id == User.id)\
        .filter(Availability.doctor_id == doctor_profile.id)\
        .filter(Appointment.status != 'cancelled')\
        .order_by(Availability.date, Availability.start_time)\
        .all()

    return render_template('doctor_dashboard.html',
                           doctor=doctor_profile,
                           availability=availability,
                           appointments=appointments,
                           user_name=session['user_name'])


# Add availability slot
@doctor.route('/doctor/availability/add', methods=['POST'])
@doctor_required
def add_availability():
    doctor_profile = Doctor.query.filter_by(user_id=session['user_id']).first()

    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']

    # Check for overlapping slots
    existing = Availability.query.filter_by(
        doctor_id=doctor_profile.id,
        date=datetime.strptime(date, '%Y-%m-%d').date()
    ).all()

    for slot in existing:
        if not (end_time <= str(slot.start_time) or start_time >= str(slot.end_time)):
            return redirect(url_for('doctor.dashboard'))

    new_slot = Availability(
        doctor_id=doctor_profile.id,
        date=datetime.strptime(date, '%Y-%m-%d').date(),
        start_time=datetime.strptime(start_time, '%H:%M').time(),
        end_time=datetime.strptime(end_time, '%H:%M').time(),
        is_booked=False
    )

    db.session.add(new_slot)
    db.session.commit()

    return redirect(url_for('doctor.dashboard'))


# Delete availability slot
@doctor.route('/doctor/availability/delete/<int:slot_id>', methods=['POST'])
@doctor_required
def delete_availability(slot_id):
    slot = Availability.query.get(slot_id)
    doctor_profile = Doctor.query.filter_by(user_id=session['user_id']).first()

    if not slot or slot.doctor_id != doctor_profile.id:
        return redirect(url_for('doctor.dashboard'))

    # Don't delete already booked slots
    if slot.is_booked:
        return redirect(url_for('doctor.dashboard'))

    db.session.delete(slot)
    db.session.commit()

    return redirect(url_for('doctor.dashboard'))