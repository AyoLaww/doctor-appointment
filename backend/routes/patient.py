from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from models import db, Appointment, Availability, Doctor, User

patient = Blueprint('patient', __name__)

# Protect route - only patients can access
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


# Patient dashboard
@patient.route('/patient/dashboard')
@patient_required
def dashboard():
    # Get all doctors
    doctors = db.session.query(Doctor, User).join(User).all()

    # Get patient's appointments
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


# Get available slots for a doctor
@patient.route('/patient/slots/<int:doctor_id>')
@patient_required
def get_slots(doctor_id):
    slots = Availability.query.filter_by(
        doctor_id=doctor_id,
        is_booked=False
    ).all()

    return jsonify([{
        'id': slot.id,
        'date': str(slot.date),
        'start_time': str(slot.start_time),
        'end_time': str(slot.end_time)
    } for slot in slots])


# Book an appointment
@patient.route('/patient/book', methods=['POST'])
@patient_required
def book():
    availability_id = request.form['availability_id']
    notes = request.form.get('notes', '')

    # Check slot is still available
    slot = Availability.query.get(availability_id)
    if not slot or slot.is_booked:
        return redirect(url_for('patient.dashboard'))

    # Create appointment
    appointment = Appointment(
        patient_id=session['user_id'],
        availability_id=availability_id,
        notes=notes,
        status='confirmed'
    )

    # Mark slot as booked
    slot.is_booked = True

    db.session.add(appointment)
    db.session.commit()

    return redirect(url_for('patient.dashboard'))


# Cancel an appointment
@patient.route('/patient/cancel/<int:appointment_id>', methods=['POST'])
@patient_required
def cancel(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    # Make sure this appointment belongs to the logged in patient
    if not appointment or appointment.patient_id != session['user_id']:
        return redirect(url_for('patient.dashboard'))

    # Free up the slot
    slot = Availability.query.get(appointment.availability_id)
    if slot:
        slot.is_booked = False

    # Cancel the appointment
    appointment.status = 'cancelled'
    db.session.commit()

    return redirect(url_for('patient.dashboard'))