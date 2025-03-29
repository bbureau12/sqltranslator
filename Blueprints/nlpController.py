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
from nlp_service import Nlp_Service
from synonymRepository import SynonymRepository

setting_repository = SettingRepository()
sql_repository = SqlRepository(setting_repository.connectionString)
synonym_repository = SynonymRepository(setting_repository.connectionString)
nlp_service = Nlp_Service(setting_repository, synonym_repository)

open_ai_service= OpenAiService(setting_repository, sql_repository)

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

    phrase = req['phrase']
    all_routes = request.args.get('allRoutes', default='false', type=str).lower() == 'true'

    result = initialize_result(phrase)

    result = handle_nlp(phrase, result)

    if all_routes or not result["nlp_result"] or result["nlp_error"]:
        result = handle_openai(phrase, result)

    return ResponseHelper.create_payload_response(result)

def initialize_result(phrase):
    return {
        "user_request": phrase,
        "nlp_query": None,
        "nlp_error": None,
        "nlp_result": None,
        "openai_query": None,
        "openai_error": None,
        "openai_result": None
    }

def handle_nlp(phrase, result):
    try:
        result["nlp_query"] = nlp_service.convert_to_sql(phrase)
    except Exception as e:
        result["nlp_error"] = f'NLP error for "{phrase}": {e}'
        return result

    if result["nlp_query"]:
        nlp_results = []
        for query in result["nlp_query"]:
            try:
                query_result = sql_repository.getSqlResult(query)
                if query_result:
                    nlp_results.append(query_result)
            except Exception as e:
                result["nlp_error"] = f'SQL error on NLP query "{query}": {e}'

        if nlp_results:
            result["nlp_result"] = nlp_results[0]
    return result

def handle_openai(phrase, result):
    try:
        result["openai_query"] = open_ai_service.convert_to_sql(phrase)
    except Exception as e:
        result["openai_error"] = f'OpenAI error for "{phrase}": {e}'
        return result

    if result["openai_query"]:
        if not result["openai_query"].strip().upper().startswith("SELECT"):
            result["openai_error"] = f'Unsafe or invalid SQL: {result["openai_query"]}'
        else:
            try:
                openai_result = sql_repository.getSqlResult(result["openai_query"])
                if openai_result:
                    result["openai_result"] = openai_result
            except Exception as e:
                result["openai_error"] = f'SQL error on OpenAI query "{result["openai_query"]}": {e}'
    return result