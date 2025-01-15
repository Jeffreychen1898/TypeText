from flask import request
import flask
import jwt

from worker.communication import ServerCommunication
from worker.trigram_partitions import TrigramPartitions

import worker

server_communication = None

# WARNING: setting coworkers is not tested

def onload():
    global trigram_partitions
    trigram_partitions = TrigramPartitions()
    server_communication = ServerCommunication(trigram_partitions)

@worker.app.route("/")
def home():
    return flask.jsonify({"a": "adsfasdf"})

@worker.app.route("/new/coworker")
def new_coworker():
    if server_communication is None:
        return flask.jsonify({
            "error": "Internal server error!",
        })

    # verify the token
    token = request.json["token"]
    try:
        token_decoded = jwt.decode(token, server_communication.get_verification_key())
        server_communication.set_verificiation_key(token_decoded["token"])
    except Exception as e:
        print(e)
        return flask.jsonify({
            "error": "Verification failed!",
            "text": "",
        })

    # appending the new coworker
    for coworker in token["coworkers"]:
        trigram_partitions.add_service(coworker)

@worker.app.route("/generate", methods=["POST"])
def generate_text():
    # if the server is not properly configured ... for some reason
    if server_communication is None:
        return flask.jsonify({
            "error": "Internal server error!",
            "text": ""
        })

    # verify the token
    token = request.json["token"]
    try:
        verification_key = jwt.decode(token, server_communication.get_verification_key())
        server_communication.set_verificiation_key(verification_key)
    except Exception as e:
        print(e)
        return flask.jsonify({
            "error": "Verification failed!",
            "text": ""
        })

    # generate and return the text
    text = trigram_partitions.retrieve_text()
    return flask.jsonify({
        "error": None,
        "text": text,
    })

@worker.app.route("/retrieve/edge")
def retrieve_trigram():
    trigram_id = request.args.get("trigram", "-1")

    try:
        trigram_id = int(trigram_id)
    except ValueError as e:
        return flask.jsonify({
            "error": "Invalid id!",
            "begin": 0,
            "num_edges": 0,
            "frequency": 0,
            "words": ["", "", ""],
        })

    if trigram_id == -1 or trigram_partitions is None:
        return flask.jsonify({
            "error": "Unable to retrieve the trigram!",
            "begin": 0,
            "num_edges": 0,
            "frequency": 0,
            "words": ["", "", ""],
        }), 404

    trigram_info = trigram_partitions.get_trigram(trigram_id)
    if trigram_info == {}:
        return flask.jsonify({
            "error": "The trigram is not found!",
            "begin": 0,
            "num_edges": 0,
            "frequency": 0,
            "words": ["", "", ""],
        }), 404

    return flask.jsonify({
        "error": "",
        "begin": trigram_info["edge_id"],
        "num_edges": trigram_info["num_edges"],
        "frequency": trigram_info["frequency"],
        "words": trigram_info["trigram"],
    })
