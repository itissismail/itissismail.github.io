import uuid
import base64
from jwcrypto import jwk
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# 1. Generate RSA key (RS384 requires at least 384 bits, but 2048 is standard)
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# 2. Export private and public keys
private_pem = key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

public_key = key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# 3. Create JWKS using jwcrypto
key_id = str(uuid.uuid4())

jwk_key = jwk.JWK.from_pem(public_pem)
jwk_key.kid = key_id
jwk_key.alg = "RS384"
jwk_key.use = "sig"  # typically "sig" for signing

# 4. Build JWKS
jwks = {
    "keys": [jwk_key.export(as_dict=True)]
}

# Output
print("----- PRIVATE KEY PEM -----")
print(private_pem.decode())

print("\n----- PUBLIC KEY PEM -----")
print(public_pem.decode())

print("\n----- JWKS -----")
import json
print(json.dumps(jwks, indent=2))

