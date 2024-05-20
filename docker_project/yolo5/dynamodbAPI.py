import boto3
from sec import secret_keys
import os
class dynamodbAPI:
    def __init__(self):
        self.client = boto3.client('dynamodb', region_name=os.environ['REGION_NAME'])
        self.tableName = os.environ['DYNAMO_TBL']
    

    def put_item(self,Item: dict):
        response = self.client.put_item(
                        TableName=self.tableName,
                        Item=Item)
        return response