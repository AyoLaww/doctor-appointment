from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
from models import db, Appointment, Availability, Doctor, User

patient = Blueprint('patient', __name__)

def patient_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'patient':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@patient.route('/patient/dashboard')
@patient_required
def dashboard():
    doctors = db.session.query(Doctor, User).join(User).all()
    appointments = db.session.query(Appointment, Availability, Doctor, User)\
        .join(Availability, Appointment.availability_id == Availability.id)\
        .join(Doctor, Availability.doctor_id == Doctor.id)\
        .join(User, Doctor.user_id == User.id)\
        .filter(Appointment.patient_id == session['user_id'])\
        .all()

    return render_template('patient_dashboard.html',
                           doctors=doctors,
                           appointments=appointments,
                           user_name=session['user_name'])


@patient.route('/patient/slots/<int:doctor_id>')
@patient_required
def get_slots(doctor_id):
    slots = Availability.query.filter_by(doctor_id=doctor_id, is_booked=False).all()
    return jsonify([{
        'id': slot.id,
        'date': str(slot.date),
        'start_time': str(slot.start_time),
        'end_time': str(slot.end_time)
    } for slot in slots])


@patient.route('/patient/book', methods=['POST'])
@patient_required
def book():
    availability_id = request.form.get('availability_id')
    notes = request.form.get('notes', '').strip()

    if not availability_id:
        flash('Please select a time slot.', 'error')
        return redirect(url_for('patient.dashboard'))

    slot = Availability.query.get(availability_id)

    if not slot:
        flash('This slot does not exist.', 'error')
        return redirect(url_for('patient.dashboard'))

    if slot.is_booked:
        flash('This slot has just been booked by someone else. Please choose another.', 'error')
        return redirect(url_for('patient.dashboard'))

    appointment = Appointment(
        patient_id=session['user_id'],
        availability_id=availability_id,
        notes=notes,
        status='confirmed'
    )
    slot.is_booked = True
    db.session.add(appointment)
    db.session.commit()
    flash('Appointment booked successfully!', 'success')
    return redirect(url_for('patient.dashboard'))


@patient.route('/patient/cancel/<int:appointment_id>', methods=['POST'])
@patient_required
def cancel(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    if not appointment or appointment.patient_id != session['user_id']:
        flash('Appointment not found.', 'error')
        return redirect(url_for('patient.dashboard'))

    slot = Availability.query.get(appointment.availability_id)
    if slot:
        slot.is_booked = False

    appointment.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('patient.dashboard'))