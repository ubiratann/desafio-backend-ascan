import mysql.connector
import os
import logging
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from mysql.connector import Error

USER     = os.environ.get("MYSQL_USER", "root")
PASSWORD = os.environ.get("MYSQL_PASSWORD", "p4ss@word")
HOST     = os.environ.get("MYSQL_HOST", "localhost")
DATABASE = os.environ.get("MYSQL_DATABASE", "subscriptions")

class DatabaseConnector:

    def __init__(self) -> None:  
        try:
            self.connection: MySQLConnection = mysql.connector.connect(host=HOST,
                                                                       database=DATABASE,
                                                                       user=USER,
                                                                       password=PASSWORD,
                                                                       autocommit=True)
        except Error as err:
            logging.error(err)

    def get_cursor(self) -> MySQLCursor:
        return self.connection.cursor(dictionary=True, buffered=True)

    def close_connection(self) -> None:
        self.connection.close()