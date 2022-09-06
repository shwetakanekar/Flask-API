from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://master:@localhost:3306/patient'
db = SQLAlchemy(app)


# Patient model
class PatientModel(db.Model):
    __tablename__ = "patient"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self.id

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"Patient(name = {self.name}, age = {self.age})"


# db.create_all()


# Patient schema
class PatientSchema(SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model = PatientModel
        sqla_session = db.session
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    age = fields.Integer(required=True)


# get all patients
@app.route('/patients', methods=['GET'])
def getAllPatients():
    patients = PatientModel.query.all()
    patient_schema = PatientSchema(many=True)
    result = patient_schema.dump(patients)
    return result


# get a patient by id
@app.route('/patients/<id>', methods=['GET'])
def getPatientById(id):
    patient = PatientModel.query.get(id)
    if patient:
        patient_schema = PatientSchema()
        result = patient_schema.dump(patient)
        return result
    return jsonify({'message': 'Patient not found'}), 404


# create new patient
@app.route('/patients', methods=['POST'])
def createPatient():
    data = request.get_json()
    if data and 'name' in data and 'age' in data:
        patient_schema = PatientSchema()
        patient = PatientModel(data['name'], data['age'])
        created_patient = patient_schema.dump(patient.create())
        return created_patient, 201
    return jsonify({'message': 'name and age is required'}), 400


# update patient
@app.route('/patients/<id>', methods=['PUT'])
def updatePatient(id):
    data = request.get_json()
    patient = PatientModel.query.get(id)
    if patient is None:
        return jsonify({'message': 'Patient not found'}), 404
    if data.get('name'):
        patient.name = data['name']
    if data.get('age'):
        patient.age = data['age']
    patient_schema = PatientSchema()
    updated_patient = patient_schema.dump(patient.create())
    return updated_patient


# delete patient
@app.route('/patients/<id>', methods=['DELETE'])
def deletePatient(id):
    patient = PatientModel.query.get(id)
    if patient is None:
        return jsonify({'message': 'Patient not found'}), 404
    patient.delete()
    return jsonify({'message': f'Patient with id={id} is deleted.'})


app.run(debug=True)
