import pymongo
import os

connection_string = os.environ['CONNECTION_STRING']
class mongoAPI:
    def __init__(self,  username, password, database, collection):
        self.database = database
        self.collection = collection
        self.username = username
        self.password = password
        self.client = pymongo.MongoClient(
            f"mongodb://{self.username}:{self.password}@{connection_string}"
            )
        # Initialize the database, and create collection if it does not exist
        self.db = self.client[self.database]

        if self.collection not in self.db.list_collection_names():
            self.db.create_collection(self.collection)
            self.collection = self.db[self.collection]
        else:
            self.collection = self.db[self.collection]

    def insert_prediction(self, pred):
        self.collection.insert_one(pred)
        return
    def insert_document(self, chat_id):
        self.collection.insert_one({"chat_id":f"{chat_id}","chat_history":[]})
        return
    def get_document_by_chat_id(self,chat_id):
        return self.collection.find_one({"chat_id":f"{chat_id}"})
    def update_document_by_chat_id(self,chat_id,role_message):
        self.collection.update_one({"chat_id":f"{chat_id}"},{"$set":{"chat_history": role_message }})
    def get_database_names(self):
        return self.client.list_database_names()