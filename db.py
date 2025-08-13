from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.get_database("whatsapp")

users_col = db["users"]
messages_col = db["messages"]
contacts_col = db["contacts"]
