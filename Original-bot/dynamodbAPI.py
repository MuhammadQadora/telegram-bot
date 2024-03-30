import boto3
from sec import secret_keys


class dynamodbAPI:
    def __init__(self):
        self.client = boto3.client(
            'dynamodb', region_name=secret_keys['REGION_NAME'])
        self.tableName = secret_keys['GPT_TBL']

    def init(self, msg_chat_id, role, msg_text):
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
        return Item

    def template(self,msg_chat_id,the_list):
        Item = {
            '_id': {
                'N': str(msg_chat_id)
            },
            'chat_logs': {
                'L': the_list
            }
        }
        return Item

    def get_item(self, msg_chat_id):
        response = self.client.get_item(
            Key={
                '_id': {
                    'N': str(msg_chat_id),
                }
            },
            TableName=self.tableName
        )
        return response

    def put_item(self, Item):
        response = self.client.put_item(
            TableName=self.tableName,
            Item=Item)
        return response

    def conver_dynamodb_dictionary_to_regular(self, msg):
        response = self.get_item(msg)
        formated = []
        for i in range(len(response['Item']['chat_logs']['L'])):
            format_me = response['Item']['chat_logs']['L'][i]['M']
            formated.append(
                {"role": format_me['role']['S'], "content": format_me['content']['S']})
        return formated

    def convert_regular_dictionary_to_dynamodb(self, chat_history):
        formated = []
        for i in range(len(chat_history)):
            format_me = chat_history[i]
            formated.append(
                {'M':{'content': {'S': format_me['content']}, 'role': {'S': format_me['role']}}})
        return formated
