import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

env = os.environ

mongo = MongoClient(env.get("MONGODB_URL"), serverSelectionTimeoutMS=5000)
db = mongo["catguard"]
