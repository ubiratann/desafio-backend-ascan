import ast
import json
import time

from http import HTTPStatus
from typing import Any
from flask import Blueprint, Response, request
from marshmallow import Schema, ValidationError
from pika.exceptions import AMQPError

from api.schema.subscription import CreateSubscriptionSchema, UpdateSubscriptionSchema
from api.service.connector import Connector

DEFAULT_EXCHANGE = "SUBSCRIPTION"
DEFAULT_EXCHANGE_TYPE = "direct"

QUEUE_PURCHASED = "PURCHASED"
QUEUE_CANCELED  = "CANCELED"
QUEUE_RESTARTED = "RESTARTED"

blueprint = Blueprint("subscriptions", __name__)

@blueprint.route("/", methods=["POST"])
def create() :
    request_data = request.json
    schema       = CreateSubscriptionSchema()
    connector    = Connector(QUEUE_PURCHASED, DEFAULT_EXCHANGE, DEFAULT_EXCHANGE_TYPE)

    return send_request(schema, request_data, connector)

@blueprint.route("/cancel/<int:id>", methods=["PUT"])
def cancel(id) :
    request_data = { "subscription_id": id }

    schema    = UpdateSubscriptionSchema()
    connector = Connector(QUEUE_CANCELED, DEFAULT_EXCHANGE, DEFAULT_EXCHANGE_TYPE)
    
    return send_request(schema, request_data, connector)

@blueprint.route("/restart/<int:id>", methods=["PUT"])
def restart(id) :
    request_data = { "subscription_id": id }
    
    schema    = UpdateSubscriptionSchema()
    connector = Connector(QUEUE_RESTARTED, DEFAULT_EXCHANGE, DEFAULT_EXCHANGE_TYPE)

    return send_request(schema, request_data, connector)

@blueprint.route("/") 
def index():
    return Response(response="OK", status=HTTPStatus.OK, headers={"Content-Type": "application/json"})

def send_request(schema: Schema, request: Any, producer: Connector) -> None:
    try:
        result  = schema.load(request)
        response = producer.publish(result)
        
        return Response(response=json.dumps(response), status=HTTPStatus.OK)

    except ValidationError as err:
        return Response(response=json.dumps(err.messages), status=HTTPStatus.BAD_REQUEST)

    except AMQPError as err:
        return Response(json.dumps(err), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    finally:
        producer.close_connection()
