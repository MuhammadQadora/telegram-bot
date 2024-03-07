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

    def checkIfExeist(self, msgChatId):
        collection = self.db[self.collection]
        if collection.find_one({"chat_id": msgChatId}) is not None:
            return True
    
    def createLog(self, msgChatId):
        collection = self.db[self.collection]
        collection.insert_one({"chat_id": msgChatId, "logs": [{"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."}]})
        return

    def insertLog(self, msgChatId, role, content):
        collection = self.db[self.collection]
        collection.update_one({"chat_id": msgChatId}, {"$push": {"logs": {"role": role, "content": content}}})
        return
    
    def getLog(self, msgChatId):
        collection = self.db[self.collection]
        if collection.find_one({"chat_id": msgChatId}) is not None:
            return collection.find_one({"chat_id": msgChatId})["logs"]
        else:
            return None