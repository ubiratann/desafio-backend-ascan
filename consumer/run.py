import json
import os
from shutil import ExecError
import signal
import sys
import pika
import ast
import logging
from sqlite3 import InterfaceError
from datetime import datetime

from service.database import DatabaseConnector

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("logger")

QUERIES = {
    "INSERT" : {
        "EVENT_HISTORY": "INSERT INTO event_history (subscription_id, type) VALUES ({id}, '{type}');",
        "SUBSCRIPTION": "INSERT INTO subscription (user_id, status_id) VALUES({id}, {status});"
    },
    "UPDATE": {
        "SUBSCRIPTION": "UPDATE subscription SET status_id={status}, updated_at=now() WHERE id={id}" 
    },
    "SELECT": {
        "STATUS": "SELECT * FROM status WHERE status_name LIKE '{name}';",
        "SUBSCRIPTION": """ SELECT 
                                sub.id, 
                                us.full_name   as user, 
                                st.status_name as status, 
                                sub.created_at as 'created at', 
                                sub.updated_at as 'updated at'
                            FROM
                                subscription as sub
                            INNER JOIN
                                status st ON st.id = sub.status_id
                            INNER JOIN
                                user us ON us.id = sub.user_id
                            WHERE
                                sub.id = {id};"""
    }
}

EVENTS = {
    "SUBSCRIPTION_PURCHASED": {
        "STATUS_NAME": "ACTIVE",
        "OPERATION": "INSERT",
        "TARGET_ID": "user_id"
    },
    "SUBSCRIPTION_RESTARTED": {
        "STATUS_NAME": "ACTIVE",
        "OPERATION": "UPDATE",
        "TARGET_ID": "subscription_id"
    },
    "SUBSCRIPTION_CANCELED": {
        "STATUS_NAME": "CANCELED",
        "OPERATION": "UPDATE",
        "TARGET_ID": "subscription_id"
    }
}

def send_response(chanel, method, props, body) -> None:

    for item in body:
        if isinstance(body[item], datetime):
            body[item] =  body[item].strftime("%d/%m/%Y %H:%M:%S")

    chanel.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=json.dumps(body))


def callback(chanel, method, properties, body) -> None:

    connection = DatabaseConnector() 
    cursor     = connection.get_cursor()
    event_type = method.routing_key
    request    = json.loads(body.decode("UTF-8"))

    OPERATION   = EVENTS[event_type]["OPERATION"]
    STATUS_NAME = EVENTS[event_type]["STATUS_NAME"]
    TARGET_ID   = EVENTS[event_type]["TARGET_ID"]

    try:
        cursor.execute(operation=QUERIES["SELECT"]["STATUS"].format(name=STATUS_NAME))
        status = cursor.fetchone()
        
        cursor.execute(operation=QUERIES[OPERATION]["SUBSCRIPTION"].format(id=request[TARGET_ID], status=status["id"]))
        id = cursor.lastrowid if cursor.lastrowid > 0 else request[TARGET_ID]
        
        cursor.execute(operation=QUERIES["INSERT"]["EVENT_HISTORY"].format(type=event_type, id=id))        

        cursor.execute(operation=QUERIES["SELECT"]["SUBSCRIPTION"].format(id=id))
        response = cursor.fetchone()

        send_response(chanel, method, properties, response)

    except InterfaceError as err:
        log.error(f"{datetime.now()} {err}")

    finally:
        cursor.close()
        connection.close_connection()

if __name__ == "__main__":

    HOST     = os.environ.get("RABBITMQ_HOST", "localhost")    
    USER     = os.environ.get("RABBITMQ_USER", "guest")
    PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")

    DEFAULT_EXCHANGE      = "SUBSCRIPTION"
    DEFAULT_EXCHANGE_TYPE = "direct"

    QUEUES = ["PURCHASED", "CANCELED", "RESTARTED"]

    credentials = pika.PlainCredentials(USER, PASSWORD)
    connection  = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, 
                                                                    credentials=credentials))
    channel= connection.channel()

    log.info(f"{datetime.now()} Connection established on {HOST}")

    channel.exchange_declare(exchange=DEFAULT_EXCHANGE,
                             exchange_type=DEFAULT_EXCHANGE_TYPE,
                             durable=True)

    for queue in QUEUES:

        channel.queue_declare(queue=queue,
                              durable=True)

        channel.queue_bind(queue=queue,
                           routing_key=f"{DEFAULT_EXCHANGE}_{queue}",
                           exchange=DEFAULT_EXCHANGE)

        channel.basic_consume(queue=queue,
                              on_message_callback=callback,
                              auto_ack=True)
    
    channel.basic_qos(prefetch_count=1)
    
    def signal_handler(signal, frame):
        log.info(f"{datetime.now()} Closing connections")

        try:
            log.warning(f"{datetime.now()} Closing chanell")
            channel.close()
            log.info(f"{datetime.now()} Channel closed")

            log.warning(f"{datetime.now()} Closing connection")
            connection.close()
            log.info(f"{datetime.now()} Connection closed")
    
            sys.exit(0)
        except Exception as err:
            log.error(f"{datetime.now()} {err}")

    signal.signal(signal.SIGINT, signal_handler) 

    channel.start_consuming()
