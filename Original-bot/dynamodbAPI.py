import boto3
from sec import secret_keys
class dynamodbAPI:
    def __init__(self):
        self.client = boto3.client('dynamodb', region_name=secret_keys['region_name'])
        self.tableName = secret_keys['GPT_TBL']
    

    def put_item(self,Item: dict):
        response = self.client.put_item(
                        TableName=self.tableName,
                        Item=Item)
        return response
    

    def get_item(self,msg_chat_id):
        response = self.client.get_item(
                    Key={
                        '_id': {
                            'N': str(msg_chat_id),
                        }
                    },
                    TableName=self.tableName
                    )
        return response
    
    def create_once(self,msg_chat_id,role,msg_text):
        Item = {
                '_id': {
                    'N': str(msg_chat_id) 
                },
                'chat_logs': {
                    'L': [
                        {
                            'M': {
                                "role": {
                                    'S': str(role)
                                },
                                "content": {
                                    'S': str(msg_text)
                                }
                            }
                        }
                    ]
                }
            }
        response = self.client.put_item(
                        TableName=self.tableName,
                        Item=Item)
        return response