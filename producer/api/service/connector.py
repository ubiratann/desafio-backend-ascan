import ast
import json
import os
import uuid
import pika
from pika.exceptions import AMQPError, AMQPConnectionError

USER     = os.environ.get("RABBITMQ_USER", "guest")
PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
HOST     = os.environ.get("RABBITMQ_HOST", "localhost")

class Connector:
    def __init__(self, queue_name, exchange_name, exchange_type) -> None:
        credentials        = pika.PlainCredentials(USER, PASSWORD)
        self.exchange_type = exchange_type
        self.connection    = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, 
                                                                               credentials=credentials))
        
        self.queue_name    = queue_name
        self.routing_key   = f"{exchange_name}_{queue_name}"
        self.exchange_name = exchange_name
        self.channel       = self.connection.channel()

        self.channel.queue_declare(queue=queue_name,
                                   durable=True)

        result = self.channel.queue_declare(queue='', 
                                            exclusive=True)

        self.callback_queue = result.method.queue 

        self.channel.exchange_declare(exchange_type=exchange_type, 
                                      exchange=exchange_name, 
                                      durable=True )
        
        self.channel.queue_bind(queue=queue_name,
                                routing_key=self.routing_key,
                                exchange=exchange_name)

        self.channel.basic_consume(queue=self.callback_queue,
                                   on_message_callback=self.on_response,
                                   auto_ack=True)

        # self.connection.process_data_events(time_limit=None)

        self.response       = None
        self.correlation_id = None

    def on_response(self, chanel, method, properties, body):
        data = json.loads(body)
        self.response = json.dumps(data, sort_keys=True)

    def publish(self, message) -> None:
        self.corr_id = str(uuid.uuid4())

        self.channel.basic_publish(exchange=self.exchange_name,
                                   routing_key=self.routing_key,
                                   body=json.dumps(message),
                                   properties=pika.BasicProperties(reply_to=self.callback_queue,
                                                                   correlation_id=self.correlation_id))
        while self.response is None:
                self.connection.process_data_events(time_limit=None)
                
        return self.response
    
    def close_connection(self) -> None:
        try:
            self.connection.close()

        except Exception as err:
            print(err)