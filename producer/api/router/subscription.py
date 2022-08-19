import ast
import json
import time

from http import HTTPStatus
from typing import Any
from flask import Blueprint, Response, request
from marshmallow import Schema, ValidationError
from pika.exceptions import AMQPError

from api.schema.subscription import CreateSubscriptionSchema, UpdateSubscriptionStatusSchema
from api.service.connector import Connector

DEFAULT_EXCHANGE = "SUBSCRIPTION"
DEFAULT_EXCHANGE_TYPE = "direct"

QUEUE_PURCHASED = "PURCHASED"
QUEUE_CANCELED  = "CANCELED"
QUEUE_RESTARTED = "RESTARTED"

ACTIVE    = 1
CANCELED  = 2

blueprint = Blueprint("subscriptions", __name__)

@blueprint.route("/", methods=["POST"])
def create() :
    try:
        request_data = request.json
        schema       = CreateSubscriptionSchema()
        request_data = schema.load(request_data)

        connector    = Connector(QUEUE_PURCHASED, DEFAULT_EXCHANGE, DEFAULT_EXCHANGE_TYPE)

        return send_request(request_data, connector)

    except ValidationError as err:
        return Response(response=json.dumps(err.messages), status=HTTPStatus.BAD_REQUEST)


@blueprint.route("/<int:id>/status", methods=["PUT"])
def update(id) :
    try:
        request_data                    = request.json
        request_data["subscription_id"] = id 
        
        schema       = UpdateSubscriptionStatusSchema()
        request_data = schema.load(request_data)

        if ("canceled" not in request_data):
            request_data["canceled"] = False

        if ("restarted" not in request_data):
            request_data["restarted"] = False

        if(request_data["canceled"] and request_data["restarted"] ):
            raise ValidationError(field_name="canceled",message="The fields 'canceled' and 'restarted' cant be TRUE at the same time !")

        if(not request_data["canceled"] and not request_data["restarted"] ):
            raise ValidationError(message="The fields 'canceled' and 'restarted' cant be FALSE at the same time !")

        queue = QUEUE_CANCELED if request_data["canceled"] else QUEUE_RESTARTED
        connector = Connector(queue, DEFAULT_EXCHANGE, DEFAULT_EXCHANGE_TYPE)
        
        return send_request(request_data, connector)
    
    except ValidationError as err:
        return Response(response=json.dumps(err.messages), status=HTTPStatus.BAD_REQUEST)


@blueprint.route("/") 
def index():
    return Response(response="OK", status=HTTPStatus.OK, headers={"Content-Type": "application/json"})

def send_request(request: Any, producer: Connector) -> None:
    try:
        response = producer.publish(request)
        return Response(response=json.dumps(response), status=HTTPStatus.OK)

    except AMQPError as err:
        return Response(json.dumps(err), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    finally:
        producer.close_connection()
