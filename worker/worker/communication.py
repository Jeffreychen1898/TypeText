import os
import requests

from worker.utils import jwt_sign_symmetric
from worker.utils import rsa_keygen
from worker.utils import rsa_decrypt


class ServerCommunication:
    def __init__(self, trigram_partitions):
        self.shared_secret = os.getenv("SHARED_SECRET")
        self.host = os.getenv("HOST")
        self.port = os.getenv("PORT")
        self.webserver = os.getenv("WEBSERVER")

        self.private_key, self.public_key = rsa_keygen()
        self.webserver_verification_key = "nokey"
        self.coworkers = []

        self.register(trigram_partitions)

    def is_webserver_bound(self):
        return self.webserver != "NONE"

    def register(self, trigram_partitions):
        if self.webserver == "NONE":
            return

        # create the payload for registering
        register_payload = {
            "host": self.host,
            "port": self.port,
            "partitions": trigram_partitions.get_partition_list(),
            "public_key": self.public_key.decode("utf-8"),
        }

        # sign the payload
        register_data = {
            "payload": jwt_sign_symmetric(register_payload, self.shared_secret, 5)
        }

        # receive response
        try:
            response = requests.post(f"{self.webserver}/api/worker/register", json=register_data, timeout=5)
            message = response.json()

            self.webserver_verification_key = rsa_decrypt(message["key"], self.private_key)
            self.coworkers = message["coworkers"]

            self.webserver_verification_key = rsa_decrypt(message["key"], self.private_key)
            print(self.webserver_verification_key)

            for coworker in self.coworkers:
                trigram_partitions.add_service(coworker)
            ## TODO: reregister if failed
        except Exception as e:
            print(f"[ERROR] {e}")

    def get_verification_key(self):
        return self.webserver_verification_key

    def set_verification_key(self, key):
        decrypted_key = rsa_decrypt(key, self.private_key)
        self.webserver_verification_key = decrypted_key
