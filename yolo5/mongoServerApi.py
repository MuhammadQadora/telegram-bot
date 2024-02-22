import os
import pymongo

CONNECTION_STRING = os.environ['CONNECTION_STRING']

class mongoAPI:
    def __init__(self,  username, password, database, collection):
        self.database = database
        self.collection = collection
        self.username = username
        self.password = password
        self.client = pymongo.MongoClient(
            f"mongodb://{self.username}:{self.password}@{CONNECTION_STRING}"
        )
        # Initialize the database, and create collection if it does not exist
        self.db = self.client[self.database]

        if self.collection not in self.db.list_collection_names():
            self.db.create_collection(self.collection)

    def insert_prediction(self, pred):
        collection = self.db[self.collection]
        collection.insert_one(pred)
        return

    def get_database_names(self):
        return self.client.list_database_names()
