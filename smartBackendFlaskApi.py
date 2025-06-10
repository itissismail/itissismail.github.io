# app_flask.py
from flask import Flask, request, jsonify
import jwt, time, uuid, requests

app = Flask(__name__)
# CLIENT_ID = "YOUR_CLIENT_ID"
# TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
# FHIR_BASE = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
# PRIVATE_KEY = open("private.key", "r").read()
CLIENT_ID = "5a173eef-46a0-4d11-972a-6f5727bc22c4"
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
FHIR_BASE = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
PRIVATE_KEY = open("/Users/mismail/.ssh/smart_epic_private_key.pem", "r").read()

def create_jwt():
    now = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": TOKEN_URL,
        "exp": now + 300,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS384")


def get_access_token():
    client_assertion = create_jwt()
    data = {
        "grant_type": "client_credentials",
        "scope": "system/Patient.read system/Observation.write",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": client_assertion,
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json()["access_token"]


@app.route("/patient/<id>")
def get_patient(id):
    token = get_access_token()
    response = requests.get(f"{FHIR_BASE}/Patient/{id}", headers={"Authorization": f"Bearer {token}"})
    return jsonify(response.json())


@app.route("/observation", methods=["POST"])
def create_observation():
    token = get_access_token()
    observation = request.json
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/fhir+json"}
    response = requests.post(f"{FHIR_BASE}/Observation", headers=headers, json=observation)
    return jsonify(response.json())


if __name__ == "__main__":
    app.run(port=5000)