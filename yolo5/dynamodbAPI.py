import boto3
from sec import secret_keys

class dynamodbAPI:
    def __init__(self):
        self.client = boto3.client('dynamodb', region_name=secret_keys['REGION_NAME'])
        self.tableName = secret_keys['DYNAMO_TBL']
    

    def put_item(self,Item: dict):
        response = self.client.put_item(
                        TableName=self.tableName,
                        Item=Item)
        return response