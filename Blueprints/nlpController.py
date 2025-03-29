import os
from flask import Blueprint, jsonify, request
import sys

from flask_cors import CORS
from Helpers.ResponseHelper import *

current_dir = os.path.dirname(os.path.abspath(__file__))
repositories_dir = os.path.join(current_dir, 'Repositories')
from settingsRepository import SettingRepository
sys.path.insert(0, './Services')
from openAiService import OpenAiService
from sqlRepository import SqlRepository
from synonymRepository import SynonymRepository


setting_repository = SettingRepository()
sql_repository = SqlRepository(setting_repository.connectionString)
synonym_repository = SynonymRepository(setting_repository.connectionString)

open_ai_service= OpenAiService(setting_repository, sql_repository, synonym_repository)

nlpController = Blueprint('nlpController', __name__, url_prefix='/nlp')

cors = CORS(nlpController)

@nlpController.route("/")
def home():
    result = ResponseHelper.create_payload_response("Hello!")
    return result

@nlpController.route("/sql/conversion", methods=['OPTIONS', 'POST'])
def convert_sql():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'success'}), 200

    req = request.get_json()
    if not req or 'phrase' not in req:
        return jsonify({"error": "Invalid input"}), 400
    get_results = req.get('getResults', True)
    humanize_results = req.get('humanizeResults', False)

    phrase = req['phrase']
    
    result = open_ai_service.convert_to_sql(phrase, get_results, humanize_results)
    
    return ResponseHelper.create_payload_response(result)
