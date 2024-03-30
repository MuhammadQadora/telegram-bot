import boto3
import botocore
from loguru import logger
import SecretManager


class dynamodbAPI:
    def __init__(self):
        self.client = boto3.client(
            'dynamodb', region_name=SecretManager.secret_value['REGION_NAME'])
        self.tableName = SecretManager.secret_value['GPT_TBL']

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

    def insertLog(self, msgChatId, role, content, isStartUp: bool = False):
        if isStartUp:
            Item = {
                '_id': {'N': str(msgChatId)},
                'chat_logs': {'L': [
                    {'M': {
                        'role': {'S': str(role)},
                        'content': {'S': str(content)}
                    }}
                ]}
            }
            response = self.client.put_item(
                TableName=self.tableName,
                Item=Item
            )
        else:
            logger.info("INSERT")
            # Get the current list of logs for this chat from DynamoDB
            res = self.getLogs(str(msgChatId))
            logger.info(res)
            logDict = {
                'role': {'S': role},
                'content': {'S': content}
            }
            # If there are no logs yet, create a new list
            if not res.get("Item") or not res["Item"].get("chat_logs"):
                logList = [logDict]
            else:   # Otherwise append to existing list
                logList = res['Item']['chat_logs']['L']
                logList.append({'M': logDict})

            # Update the item in DynamoDB with the new information
            response = self.client.update_item(
                TableName=self.tableName,
                Key={'_id': {'N': str(msgChatId)}}
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
            # return response["Item"]["chat_logs"]["L"]
            return response
        except Exception as ex:
            print('ERROR in getting log from DynamoDB')
            print(ex)
            return None
