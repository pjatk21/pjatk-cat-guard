import logging
import os

from dotenv import load_dotenv
from mongoengine import connect
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from doctor import DockerDoctor

load_dotenv()


def init_connection():
    conn: MongoClient = connect(host=os.getenv('MONGODB_URL'), db='catguard', tz_aware=True, serverSelectionTimeoutMS=2000)
    try:
        conn.server_info()
        DockerDoctor('bot').update_module('db')
        DockerDoctor('web').update_module('db')
    except PyMongoError as err:
        DockerDoctor('bot').fail_module('db')
        DockerDoctor('web').fail_module('db')
        logging.critical(err)
    logging.info(conn)

