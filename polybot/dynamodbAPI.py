import boto3
import botocore
from loguru import logger
import SecretManager


class dynamodbAPI:
    def __init__(self):
        self.client = boto3.client(
            'dynamodb', region_name=SecretManager.secret_value['REGION_NAME'])
        self.tableName = SecretManager.secret_value['GPT_TBL']

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
    def checkIfExeist(self, msgChatId):
        logger.info(f"Checking {msgChatId}")
        try:
            response = self.client.get_item(
                Key={
                    '_id': {
                        'N': str(msgChatId),
                    }
                },
                TableName=self.tableName
            )
            if 'Item' in response:
                logger.info("TRUE")
                return True
            else:
                logger.info("FALSE")
                return False
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "ResourceNotFoundException":
                return False

    def insertLog(self, msgChatId, role, content):
        self.putLog(msgChatId, role, content)

        # Get the current list of logs for this chat from DynamoDB
        res = self.getLogs(str(msgChatId))
        logger.info(res)
        logDict = {
            'role': {'S': role},
            'content': {'S': content}
        }
        res.append(logDict)  # Add new log to end of list

        # Update the item in DynamoDB with the new information
        response = self.client.update_item(
            TableName=self.tableName,
            Key={'_id': {'N': str(msgChatId)}}
        )

        return response

    def putLog(self, msgChatId, userRole, userContent):
        Item = {
            '_id': {'N': str(msgChatId)},
            'chat_logs': {'L': [
                {'M': {
                    'role': {'S': str(userRole)},
                    'content': {'S': str(userContent)}
                }}
            ]}
        }
        try:
            response = self.client.put_item(
                TableName=self.tableName,
                Item=Item
            )
            return response
        except:
            logger.ERROR("ERROR ON PUT ITEM")

    def put_item(self, Item):
        response = self.client.put_item(
            TableName=self.tableName,
            Item=Item)
        return response
    
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

    def getLogs(self, msgChatId):
        try:
            response = self.client.get_item(
                Key={
                    '_id': {
                        'N': str(msgChatId)
                    }
                },
                TableName=self.tableName
            )
            return response["Item"]["chat_logs"]["L"]
        except Exception as ex:
            print('ERROR in getting log from DynamoDB')
            print(ex)
            return None

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