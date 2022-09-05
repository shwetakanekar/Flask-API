from flask import Flask, jsonify, request
app = Flask(__name__)


patients = [
    {'id': 1, 'name': 'John', 'age': 40},
    {'id': 2, 'name': 'Tom', 'age': 45},
    {'id': 3, 'name': 'Jerry', 'age': 28},
    {'id': 4, 'name': 'Alice', 'age': 36},
]


# get all patients
@app.route('/patients', methods=['GET'])
def getAllPatients():
    return jsonify(patients)


# get a patient by id
@app.route('/patients/<id>', methods=['GET'])
def getPatientById(id):
    for i in range(len(patients)):
        if patients[i]['id'] == int(id):
            return jsonify(patients[i]), 200
    return jsonify({'message': 'Patient not found'}), 404


# create new patient
@app.route('/patients', methods=['POST'])
def createPatient():
    patientData = request.get_json()
    print(patientData)
    if patientData and 'name' in patientData and 'age' in patientData:
        patientData['id'] = int(patients[-1]['id']) + 1
        patients.append(patientData)
        return patientData, 201
    return jsonify({'message': 'name and age is required'}), 400


# update patient
@app.route('/patients/<id>', methods=['PUT'])
def updatePatient(id):
    for i in range(len(patients)):
        if patients[i]['id'] == int(id):
            patientData = request.get_json()
            if patientData and 'name' in patientData and 'age' in patientData:
                patients[i]['name'] = patientData['name']
                patients[i]['age'] = patientData['age']
                return jsonify(patients[i]), 200
            return jsonify({'message': 'name and age is required'}), 400
    return jsonify({'message': 'Patient not found'}), 404


# delete patient
@app.route('/patients/<id>', methods=['DELETE'])
def deletePatient(id):
    for i in range(len(patients)):
        if patients[i]['id'] == int(id):
            patients.remove(patients[i])
            return jsonify({'message': f'Patient with id={id} is deleted.'}), 200
    return jsonify({'message': 'Patient not found'}), 404


app.run(debug=True)
