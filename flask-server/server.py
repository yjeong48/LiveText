from flask import Flask, flash, request, redirect, url_for
import flask
from flask.helpers import send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import io
import time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
import sys
import requests
import uuid
import json

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
CORS(app)
load_dotenv()
subscription_key = os.getenv('COG_SERVICE_KEY')
location = os.getenv('COG_SERVICE_REGION')


def get_text(image, computervision_client):
    read_response = computervision_client.read_in_stream(image, raw=True)
    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]

    image.close()

    i = 0
    while True:
        i += 1
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    if read_result.status == OperationStatusCodes.succeeded:
        text = ""
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                text += line.text
    return text


def detect_language(text, subscription_key, location, constructed_url):
    params = {
        "api-version": "3.0"
    }
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Ocp-Apim-Subscription-Region": location,
        "Content-type": "application/json"
    }
    body = [{
        "text": text
    }]
    request = requests.post(
        constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    language = response[0]["language"]
    print("source language is: ", response[0])
    return language


def translate(text, source_language, target_language, subscription_key, location, constructed_url):
    params = {
        'api-version': '3.0',
        'from': source_language,
        'to': target_language
    }

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{
        'text': text
    }]

    request = requests.post(
        constructed_url, params=params, headers=headers, json=body)
    response = request.json()
    translation = response[0]["translations"][0]["text"]
    return translation


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["POST", "GET"])
def my_translator():
    if request.method == 'GET':
        return flask.Response("flask server is running", headers={"Content-Type": "text/html"})
    image_path = ""
    # check if the post request has the file part
    if 'file' not in request.files:
        print("file not in request")
        return flask.Response("Request does not contain image file.", headers={"Content-Type": "text/html"})

    file = request.files['file']
    target_lang = request.form.get("targetLang")
    print(request, "\n")
    if target_lang == "":
        target_lang = "en"
    if file and allowed_file(file.filename):
        # read image file as bytes into file_like object
        image = io.BytesIO(file.read())

        # Authenticate Computer Vision client
        endpoint = "https://livetext.cognitiveservices.azure.com/"
        trans_endpoint = "https://api.cognitive.microsofttranslator.com"
        computervision_client = ComputerVisionClient(
            endpoint, CognitiveServicesCredentials(subscription_key))
        detect_constructed_url = trans_endpoint + '/detect'
        trans_constructed_url = trans_endpoint + '/translate'

        text = get_text(image, computervision_client)
        source_language = detect_language(
            text, subscription_key, location, detect_constructed_url)
        translated_text = translate(
            text, source_language, target_lang, subscription_key, location, trans_constructed_url)
        image.close()
        return flask.Response(translated_text, headers={"Content-Type": "text/html"})


if __name__ == "__main__":
    app.run(debug = False, threaded=True)
