import os
import requests

from worker.utils import jwt_sign_symmetric
from worker.utils import rsa_keygen
from worker.utils import rsa_decrypt


class ServerCommunication:
    def __init__(self):
        self.shared_secret = os.getenv("SHARED_SECRET")
        self.host = os.getenv("HOST")
        self.port = os.getenv("PORT")
        self.webserver = os.getenv("WEBSERVER")

        self.private_key, self.public_key = rsa_keygen()
        self.webserver_verification_key = ""
        self.coworkers = []

        self.register()

    def register(self):
        if self.webserver == "NONE":
            return

        # create the payload for registering
        register_payload = {
            "host": self.host,
            "port": self.port,
            "public_key": self.public_key.decode("utf-8"),
        }

        # sign the payload
        register_data = {
            "payload": jwt_sign_symmetric(register_payload, self.shared_secret, 5)
        }

        # receive response
        try:
            response = requests.post(f"{self.webserver}/api/worker/register", json=register_data)
            message = response.json()

            self.webserver_verification_key = rsa_decrypt(message["key"], self.private_key)
            self.coworkers = message["workers"]

            ## TODO: register with coworker servers
            ## TODO: reregister if failed
        except Exception as e:
            print(f"[ERROR] {e}")

    def get_verification_key(self):
        return self.webserver_verification_key

    def set_verificiation_key(self, key):
        self.webserver_verification_key = key
