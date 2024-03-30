import boto3
import botocore
from loguru import logger
import polybot.SecretManager as secret_manager

client = boto3.client(
    'dynamodb', region_name=secret_manager.secret_value['REGION_NAME'])
tbl = secret_manager.secret_value['GPT_TBL']


def checkIfExeist(msgChatId):

    logger.info("Checking")
    try:
        response = client.get_item(
            Key={
                '_id': {
                    'N': str(msgChatId),
                }
            },
            TableName=tbl
        )
        logger.info(response)

        if 'Item' in response:
            return True
        else:
            return False
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "ResourceNotFoundException":
            return False
        else:
            raise e


def getLogs(msgChatId):
    # try:
    response = client.get_item(
        Key={
            '_id': {
                'N': str(msgChatId)
            }
        },
        TableName=tbl
    )
    logger.info(type(response))
    logger.info(type(response["Item"]["chat_logs"]["L"]))
    # logger.warning("RRRR"+response["Item"]["chat_logs"]["L"])
    return response
    # except Exception as ex:
    #     print('ERROR in getting log from DynamoDB')
    #     print(ex)
    #     return None


# logger.info(checkIfExeist(146142514))
logger.info(getLogs(146142514))
