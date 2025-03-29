import json
from flask import make_response


class ResponseHelper:
    @staticmethod
    def create_payload_response(payload):
        json_payload = json.dumps(ResponseHelper.convert(payload))
        response = make_response(json_payload, 200)
        response.headers.add('Content-Type', 'application/json')
        # response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    @staticmethod
    def create_error_response(statusCode):
        response = make_response('', statusCode)
        response.headers.add('Content-Type', 'application/json')
        # response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @staticmethod
    def create_empty_response():
        response = make_response('', 204)
      ##  response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @staticmethod
    def convert(o):
        if isinstance(o, dict):
            return {key: ResponseHelper.convert(value) for key, value in o.items()}
        elif hasattr(o, '__dict__'):
            return ResponseHelper.convert(o.__dict__)
        elif hasattr(o, '__slots__'):
            return ResponseHelper.convert({slot: getattr(o, slot) for slot in o.__slots__})
        elif isinstance(o, list):
            return [ResponseHelper.convert(item) for item in o]
        else:
            return o
        
    @staticmethod
    def convertToCacheObject(o):
        response = {
            "payload": o
        }
        return json.dumps(response)
    
    @staticmethod
    def convertFromCacheObject(o):
        return json.loads(o)

    @staticmethod
    def processNullableParameter(o):
        if o.lower() == 'null':
            return None
        return o