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

def create_jwt():
    now = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "sub": CLIENT_ID,
        "aud": TOKEN_URL,
        "exp": now + 300,
        "jti": str(uuid.uuid4()),
    }
    logger.info(f"Creating JWT with payload: {payload}")
    encoded = jwt.encode(payload, PRIVATE_KEY, algorithm="RS384")
    logger.info(f"JWT with payload: {encoded}")
    return encoded

def get_access_token():
    logger.info("Requesting access token from Epic token endpoint")
    client_assertion = create_jwt()
    data = {
        "grant_type": "client_credentials",
        "scope": "system/*.read system/*.write",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": client_assertion,
    }
    response = requests.post(TOKEN_URL, data=data)
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
    token = get_access_token()
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
    token = get_access_token()
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


