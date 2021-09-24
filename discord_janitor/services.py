import os

from dotenv import load_dotenv
from pymongo import MongoClient
from sendgrid import SendGridAPIClient

load_dotenv()

env = os.environ

sg = SendGridAPIClient(env.get("SENDGRID_APIKEY"))
mongo = MongoClient(env.get("MONGODB_URL"))
db = mongo["verifications"]
