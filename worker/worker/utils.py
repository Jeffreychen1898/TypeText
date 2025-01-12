import os
import datetime
import base64
import jwt

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

def jwt_sign_symmetric(payload, secret, exptime):
    exp_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=exptime)
    payload["exp"] = exp_time

    return jwt.encode(payload, secret, algorithm="HS256")

def rsa_keygen():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return private_key, pem_public_key

def rsa_decrypt(message, private_key):
    decrypted_message = private_key.decrypt(
        base64.b64decode(message),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return decrypted_message.decode("utf-8")

def response_ok(response_code):
    return response_code > 199 and response_code < 300
