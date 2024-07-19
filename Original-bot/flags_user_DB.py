from enum import Enum
from loguru import logger
import os
import boto3
import botocore.exceptions
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
table = dynamodb.Table("flags-table-terraform-dev")


class Notify(Enum):
    CHATGPT = "chatgpt"
    GPT4 = "gpt4"
    YOLO = "yolo"
    QUESTION = "question"
    TEXT_TO_IMAGE = "textToImage"


class Member:
    name = str()
    notify = dict()

    def __init__(self, name):
        self.name = name
        self.notify = {notify: False for notify in Notify}

    def toggle_notify(self, notification):
        if notification in self.notify:
            self.notify[notification] = not self.notify[notification]
        else:
            print(f"Invalid notification type: {notification}")


def pull_data():
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    # Convert string keys back to Notify enum keys
    for item in data:
        item['notify'] = convert_dict_keys_to_enum(item['notify'])
    return data

def update_member_notify(name, notify_updates):
    try:
        # Convert enum keys to string representation for updating
        notify_updates_str = convert_enum_keys_to_str(notify_updates)

        response = table.update_item(
            Key={'_id': Decimal(name)},  # Assuming _id is the primary key
            UpdateExpression="SET notify = :notify_updates",
            ExpressionAttributeValues={
                ':notify_updates': notify_updates_str
            },
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Update succeeded: {response}")
    except Exception as e:
        logger.error(f"Error updating item: {e}")

def is_member_in_list_by_name(bot_members: list, name: str):
    for member in bot_members:
        if member['name'] == name:
            return True
    return False

def add_member(bot_members: list, name: str):
    if not is_member_in_list_by_name(bot_members, name):
        new_member = Member(name)
        bot_members.append({
            '_id': Decimal(new_member.name),
            'name': new_member.name,
            'notify': new_member.notify  # Store enum keys directly
        })
        item = {
            '_id': Decimal(new_member.name),
            'name': new_member.name,
            'notify': convert_enum_keys_to_str(new_member.notify)  # Convert enum keys to string for DynamoDB
        }
        try:
            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(#name)',
                ExpressionAttributeNames={'#name': 'name'}
            )
            logger.info(f"Added member [{item['name']}] to DynamoDB table.")
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.error(f"Item with name [{item['name']}] already exists.")
            else:
                logger.error(f"ClientError: {e.response['Error']['Message']}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

# def add_member(bot_members: list, name: str):
#     if not is_member_in_list_by_name(bot_members, name):
#         new_member = Member(name)
#         bot_members.append({
#             '_id': Decimal(new_member.name),
#             'name': new_member.name,
#             'notify': convert_enum_keys_to_str(new_member.notify)
#         })
#         item = {
#             '_id': Decimal(new_member.name),
#             'name': new_member.name,
#             'notify': convert_enum_keys_to_str(new_member.notify)
#         }
#         try:
#             table.put_item(
#                 Item=item,
#                 ConditionExpression='attribute_not_exists(#name)',
#                 ExpressionAttributeNames={'#name': 'name'}
#             )
#             logger.info(f"Added member [{item['name']}] to DynamoDB table.")
#         except botocore.exceptions.ClientError as e:
#             if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
#                 logger.error(
#                     f"Item with name [{item['name']}] already exists.")
#             else:
#                 logger.error(f"ClientError: {e.response['Error']['Message']}")
#         except Exception as e:
#             logger.error(f"Unexpected error: {e}")

def convert_notify_to_str(notify=Notify):
    # Convert notify dictionary to ensure all values are strings
    notify = {k: str(v) for k, v in notify.items()}

def convert_dict_keys_to_enum(original_dict):
    return {Notify[key]: value for key, value in original_dict.items()}

def convert_enum_keys_to_str(enum_dict):
    return {key.name: value for key, value in enum_dict.items()}

def get_member_from_dynamo(name):
    try:
        response = table.get_item(Key={'_id': Decimal(name)})
        if 'Item' in response:
            item = response['Item']
            item['notify'] = convert_dict_keys_to_enum(item['notify'])
            return item
        else:
            logger.warning(f"Member with name [{name}] not found.")
            return None
    except Exception as e:
        logger.error(f"Error retrieving item: {e}")
        return None

def get_member_by_name(member_list: list, name: str):
    # Get the first Member object from the list with the given name.5
    for member in member_list:
        if member['name'] == name:
            logger.warning("FOUND")
            m = Member(name)
            m.notify = member['notify']
            logger.warning(m.notify)
            return m
    return None  # Return None if no member with the specified name is found


def get_notify_by_member_name(member_list: list, name: str):
    # Get the first Member object from the list with the given name.5
    for member in member_list:
        if member['name'] == name:
            return member['notify']
    return None  # Return None if no member with the specified name is found
