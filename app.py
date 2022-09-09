from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from functools import wraps
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = '261bafc16917748597b1e3c81347a873'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://master:@localhost:3306/patient'
db = SQLAlchemy(app)


# Patient model
class PatientModel(db.Model):
    __tablename__ = "patient"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self.id

    def __init__(self, name, age, username, password):
        self.name = name
        self.age = age
        self.username = username
        self.password = password

    def __repr__(self):
        return f"Patient(name = {self.name}, age = {self.age})"


class AppointmentModel(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    from_datetime = db.Column(db.DateTime, nullable=False)
    to_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, from_datetime, to_datetime, patient_id):
        self.from_datetime = from_datetime
        self.to_datetime = to_datetime
        self.patient_id = patient_id

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self.id


db.create_all()


# Patient schema
class PatientSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = PatientModel
        sqla_session = db.session
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    age = fields.Integer(required=True)
    username = fields.String(required=True)
    password = fields.String(required=True)


class AppointmentSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = AppointmentModel
        sqla_session = db.session
    id = fields.Integer(dump_only=True)
    patient_id = fields.Integer(dump_only=True)
    from_datetime = fields.DateTime(required=True)
    to_datetime = fields.DateTime(required=True)


# decorator to validate token
def validate_token(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'Token is missing.'}), 400

        try:
           data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
           current_patient = PatientModel.query.filter_by(id=data['id']).first()
        except:
           return jsonify({'message': 'Token is invalid.'}), 403
        return f(current_patient, *args, **kwargs)
    return decorator


# get all patients
@app.route('/patients', methods=['GET'])
def getAllPatients():
    try:
        patients = PatientModel.query.all()
        patient_schema = PatientSchema(many=True)
        result = patient_schema.dump(patients)
        return jsonify(result)
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# get a patient by id
@app.route('/patients/<id>', methods=['GET'])
def getPatientById(id):
    try:
        patient = PatientModel.query.get(id)
        if patient:
            patient_schema = PatientSchema()
            result = patient_schema.dump(patient)
            return result
        return jsonify({'message': 'Patient not found.'}), 404
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# create new patient
# @app.route('/patients', methods=['POST'])
# def createPatient():
#     try:
#         data = request.get_json()
#         if data and 'name' in data and 'age' in data and 'username' in data and 'password' in data:
#             patient_schema = PatientSchema()
#             hashed_password = generate_password_hash(data['password'], method='sha256')
#             patient = PatientModel(data['name'], data['age'], data['username'], hashed_password)
#             created_patient = patient_schema.dump(patient.create())
#             return created_patient, 201
#         return jsonify({'message': 'name, username, age and password is required.'}), 400
#     except:
#         return jsonify({'message': 'An unexpected error occured'}), 500


# update patient
@app.route('/patients/<id>', methods=['PUT'])
@validate_token
def updatePatient(current_patient, id):
    try:
        data = request.get_json()
        patient = PatientModel.query.get(id)
        if patient is None:
            return jsonify({'message': 'Patient not found.'}), 404
        if id != str(current_patient.id):
            return jsonify({'message': 'You are not authorized to update other patient.'}), 401 
        if data.get('name'):
            patient.name = data['name']
        if data.get('age'):
            patient.age = data['age']
        if data.get('username'):
            patient.username = data['username']
        if data.get('password'):
            patient.password = generate_password_hash(data['password'], method='sha256')
        patient_schema = PatientSchema()
        updated_patient = patient_schema.dump(patient.create())
        return updated_patient
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# delete patient
@app.route('/patients/<id>', methods=['DELETE'])
@validate_token
def deletePatient(current_patient, id):
    try:
        patient = PatientModel.query.get(id)
        if patient is None:
            return jsonify({'message': 'Patient not found.'}), 404
        if id != str(current_patient.id):
            return jsonify({'message': 'You are not authorized to delete other patient.'}), 401   
        patient.delete()
        return jsonify({'message': f'Patient with id={id} is deleted.'})
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# register a new patient
@app.route('/sign_up', methods=['POST'])
def sign_up():
    try:
        data = request.get_json()
        if data and 'name' in data and 'username' in data and 'age' in data and 'password' in data:
            hashed_password = generate_password_hash(data['password'], method='sha256')
            patient = PatientModel(data['name'], data['age'], data['username'], hashed_password)
            patient_schema = PatientSchema()
            try:
                patient_schema.dump(patient.create())
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'Username is taken.'}), 400
            return jsonify({'message': 'Patient registered successfully.'}), 201
        return jsonify({'message': 'name, username, password and age is required.'}), 400
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# sign in API
@app.route('/sign_in', methods=['POST'])
def sign_in():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data: 
            return jsonify({'message': 'username and password is required.'}), 400
        
        patient = PatientModel.query.filter_by(username=data['username']).first()  
        if check_password_hash(patient.password, data['password']):
            token = jwt.encode({'id' : patient.id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=15)}, app.config['SECRET_KEY'], "HS256") 
            return jsonify({'token' : token})
    
        return jsonify({'message': 'Invalid username and password.'}), 403
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# Create an appointment
@app.route('/appointments', methods=['POST'])
@validate_token
def createAppointment(current_patient):
    try:
        data = request.get_json()
        if not data or 'from_datetime' not in data or 'to_datetime' not in data:
            return jsonify({'message': 'from_datetime and to_datetime is required.'}), 400
        appointment_schema = AppointmentSchema()
        appointment = AppointmentModel(data['from_datetime'], data['to_datetime'], current_patient.id)
        appointment_schema.dump(appointment.create())
        return jsonify({'message': 'Appointment created successfully.'})
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# Get all appointments
@app.route('/appointments', methods=['GET'])
@validate_token
def getAppointments(current_patient):
    try:
        appointments = AppointmentModel.query.filter_by(patient_id=current_patient.id)
        appointment_schema = AppointmentSchema(many=True)
        result = appointment_schema.dump(appointments)
        return jsonify(result)
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


# Delete an appointment
@app.route('/appointments/<id>', methods=['DELETE'])
@validate_token
def deleteAppointment(current_patient, id):
    try:
        appointment = AppointmentModel.query.get(id)
        if not appointment:
            return jsonify({'message': 'Appointment not found.'}), 404
        if appointment.patient_id != current_patient.id:
            return jsonify({'message': 'You are not authorized to delete other patient\'s appointment.'}), 401    
        appointment.delete()
        return jsonify({'message': 'Appointment deleted successfully.'})
    except:
        return jsonify({'message': 'An unexpected error occured'}), 500


app.run(debug=True)
