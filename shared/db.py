import os

from dotenv import load_dotenv
from mongoengine import connect

load_dotenv()


def init_connection():
    connect(host=os.getenv('MONGODB_URL'), db='catguard21')
