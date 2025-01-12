from dotenv import load_dotenv
import flask

# Load the environment variables
load_dotenv()

# Create the flask app
app = flask.Flask(__name__)

import worker.server

worker.server.onload()
