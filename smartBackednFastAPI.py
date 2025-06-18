from fastapi import FastAPI, Request
import jwt, time, uuid, requests, logging
import json
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow all origins (for testing; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify list like ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CLIENT_ID = "5a173eef-46a0-4d11-972a-6f5727bc22c4"
TOKEN_URL = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
FHIR_BASE = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
PRIVATE_KEY_PATH = "/Users/mismail/.ssh/smart_epic_private_key.pem"
logger.info(f"Loading private key from {PRIVATE_KEY_PATH}")
PRIVATE_KEY = open(PRIVATE_KEY_PATH, "r").read()
#logger.info(f"Private key loaded {PRIVATE_KEY}")

def create_jwt(client_id,token_url):
    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": token_url,
        "exp": now + 300,
        "jti": str(uuid.uuid4()),
    }
    logger.info(f"Creating JWT with payload: {payload}")
    encoded = jwt.encode(payload, PRIVATE_KEY, algorithm="RS384", headers={
        "typ": "JWT",
        "kid": "1EBx0b3f8kKtQAW7NdbiA7Tx17yuyxWa"   
    })
    logger.info(f"JWT with payload: {encoded}")
    return encoded

def get_access_token(client_id,token_url):
    logger.info(f"Requesting access token from token endpoint using client_id: {client_id} and token_url {token_url}")
    client_assertion = create_jwt(client_id,token_url)
    data = {
        "grant_type": "client_credentials",
        "scope": "system/Patient.read system/Condition.write",
        #"scope": "system/*.read system/*.write",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": client_assertion,
    }
    logger.info(f"Requesting token : {token_url}")
    response = requests.post(token_url, data=data)
    logger.info(f"Token endpoint response: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"Failed to get access token: {response.text}")
        raise Exception("Access token error")
    token = response.json()["access_token"]
    logger.info("Access token obtained successfully"+token);
    return token

@app.get("/patient/{id}")
def get_patient(id: str):
    logger.info(f"Fetching Patient resource for ID: {id}")
    token = get_access_token(CLIENT_ID,TOKEN_URL)
    url = f"{FHIR_BASE}/Patient/{id}"
    logger.info(f"GET {url}")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
    response = requests.get(url, headers=headers)
    logger.info(f"Response: {response.status_code}")
    logger.info(f"Raw response text: {response.text}")

    try:
        return response.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
    return {"msg": "Failed to parse response", "text": response.text}

    #return response.json()

@app.post("/condition")
async def create_condition(request: Request):
    logger.info("Received request to create Condition")
    token = get_access_token(CLIENT_ID,TOKEN_URL)
    obs_data = await request.json()
    logger.info(f"Condition Payload: {json.dumps(obs_data, indent=2)}")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/fhir+json"}
    response = requests.post(f"{FHIR_BASE}/Condition", headers=headers, json=obs_data)
    logger.info(f"Observation POST response: {response.status_code}")
    logger.info(f"Observation Raw response text: {response.text}")
    try:
        return response.json()
    except Exception as e:
        logger.error(f"No Response or Failed to parse JSON: {e}")
    return {"msg": "No or Failed to parse Response", "code": response.status_code}



# ---------------------------
# Cerners's Backend FHIR Call
# ---------------------------

CERNER_CLIENT_ID = "41c675a4-ecc6-4b31-afb3-c7482f3e4dc4"
CERNER_CLIENT_SECRET = "secret"
CERNER_TOKEN_URL = "https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/token"
CERNER_FHIR_BASE = "https://fhir-ehr-code.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d"  # Adjust if using production



@app.get("/cerner/patient/{patient_id}")
def get_patient_from_cerner(patient_id: str):
    logger.info(f"Fetching Patient resource from Cerner for ID: {id}")
    token = get_access_token(CERNER_CLIENT_ID,CERNER_TOKEN_URL)
    url = f"{CERNER_FHIR_BASE}/Patient/{patient_id}"
    logger.info(f"GET {url}")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
    response = requests.get(url, headers=headers)
    logger.info(f"Response: {response.status_code}")
    logger.info(f"Raw response text: {response.text}")

    try:
        return response.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
    return {"msg": "Failed to parse response", "text": response.text}

@app.post("/cerner/condition")
async def create_condition(request: Request):
    logger.info("Received request to create Condition on Cerner")
    token = get_access_token(CERNER_CLIENT_ID,CERNER_TOKEN_URL)
    obs_data = await request.json()
    logger.info(f"Condition Payload: {json.dumps(obs_data, indent=2)}")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/fhir+json"}
    response = requests.post(f"{CERNER_FHIR_BASE}/Condition", headers=headers, json=obs_data)
    logger.info(f"Observation POST response: {response.status_code}")
    logger.info(f"Observation Raw response text: {response.text}")
    try:
        return response.json()
    except Exception as e:
        logger.error(f"No Response or Failed to parse JSON: {e}")
    return {"msg": "No or Failed to parse Response", "code": response.status_code}