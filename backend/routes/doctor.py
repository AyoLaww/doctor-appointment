from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models import db, Availability, Appointment, User, Doctor
from datetime import datetime

doctor = Blueprint('doctor', __name__)

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


@doctor.route('/doctor/dashboard')
@doctor_required
def dashboard():
    doctor_profile = Doctor.query.filter_by(user_id=session['user_id']).first()
    availability = Availability.query.filter_by(
        doctor_id=doctor_profile.id
    ).order_by(Availability.date, Availability.start_time).all()

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


@doctor.route('/doctor/availability/add', methods=['POST'])
@doctor_required
def add_availability():
    doctor_profile = Doctor.query.filter_by(user_id=session['user_id']).first()

    date = request.form.get('date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')

    # Validation
    if not date or not start_time or not end_time:
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('doctor.dashboard'))

    if start_time >= end_time:
        flash('End time must be after start time.', 'error')
        return redirect(url_for('doctor.dashboard'))

    parsed_date = datetime.strptime(date, '%Y-%m-%d').date()

    if parsed_date < datetime.today().date():
        flash('You cannot add slots for past dates.', 'error')
        return redirect(url_for('doctor.dashboard'))

    # Check for overlapping slots
    existing = Availability.query.filter_by(
        doctor_id=doctor_profile.id,
        date=parsed_date
    ).all()

    for slot in existing:
        if not (end_time <= str(slot.start_time) or start_time >= str(slot.end_time)):
            flash('This slot overlaps with an existing slot.', 'error')
            return redirect(url_for('doctor.dashboard'))

    new_slot = Availability(
        doctor_id=doctor_profile.id,
        date=parsed_date,
        start_time=datetime.strptime(start_time, '%H:%M').time(),
        end_time=datetime.strptime(end_time, '%H:%M').time(),
        is_booked=False
    )

    db.session.add(new_slot)
    db.session.commit()
    flash('Availability slot added successfully!', 'success')
    return redirect(url_for('doctor.dashboard'))


@doctor.route('/doctor/availability/delete/<int:slot_id>', methods=['POST'])
@doctor_required
def delete_availability(slot_id):
    slot = Availability.query.get(slot_id)
    doctor_profile = Doctor.query.filter_by(user_id=session['user_id']).first()

    if not slot or slot.doctor_id != doctor_profile.id:
        flash('Slot not found.', 'error')
        return redirect(url_for('doctor.dashboard'))

    if slot.is_booked:
        flash('Cannot delete a slot that is already booked.', 'error')
        return redirect(url_for('doctor.dashboard'))

    db.session.delete(slot)
    db.session.commit()
    flash('Slot deleted successfully.', 'success')
    return redirect(url_for('doctor.dashboard'))