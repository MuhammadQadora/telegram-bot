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
    # Scan the table to retrieve all items
    response = table.scan()
    data = response['Items']

    # Continue scanning if there are more items (pagination)
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data


def update_member_notify(name, notify_updates):
    notify_updates = convert_notify_to_str(notify_updates)
    try:
        response = table.update_item(
            Key={'name': name},
            UpdateExpression="SET notify = :notify_updates",
            ExpressionAttributeValues={
                ':notify_updates': notify_updates
            },
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"Update succeeded: {response}")
    except Exception as e:
        logger.error(f"Error updating item: {e}")


def is_member_in_list_by_name(bot_members: list, name: str):
    logger.info(f"CHECKING LOCAL LIST, IF CONTAINS {name}\n {bot_members}")
    # Check if a member object with a given name exists in the list.
    
    for member in bot_members:
        logger.error(type(member))
        logger.warning(member['name'])
        if member['name'] == name:
            logger.error("TRUE")
            return True
    logger.error("FALSE")
    return False


def add_member(bot_members: list, name: str):
    logger.warning(f"ADD_MEMBER_START_WITH : {len(bot_members)}")
    logger.warning(f"ADD_MEMBER_START_WITH : {type(bot_members)}")
    # Add a new member to the list if it doesn't already exist
    new_member = Member(name)
    found = False
    for lmembers in bot_members:
        logger.info(type(lmembers))
        if lmembers['name'] == name:
            found = True
            break
    
    logger.warning(f"{found}")
    if found == False:
        logger.error("ENTERED")
        # bot_members.append(new_member)
        bot_members.append({
            '_id': Decimal(new_member.name),
            'name': new_member.name,
            'notify': str(new_member.notify)
        })
    
    item = {
        '_id': new_member.name,
        'name': str(new_member.name),
        'notify': str(new_member.notify)
    }
    # try:
    #     table.put_item(Item=item)
    #     logger.info(f"Added member [{name}] to DynamoDB table.")
    # except botocore.exceptions.ClientError as e:
    #     logger.error(f"Error adding [{name}] to DynamoDB table: {e}")
    try:
        table.put_item(
            Item=item,
            # Use expression attribute name
            ConditionExpression='attribute_not_exists(#name)',
            ExpressionAttributeNames={
                '#name': 'name'
            }
        )
        logger.info(f"Added member [{item['name']}] to DynamoDB table.")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.error(f"Error adding [{
                         item['name']}] to DynamoDB table: Item with this name already exists.")
        else:
            # Extract error code and message
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"ClientError adding [{item['name']}] to DynamoDB table: {
                         error_code} - {error_message}")
    except Exception as e:
        # Log unexpected exceptions
        logger.error(f"Unexpected error adding [{
                     item['name']}] to DynamoDB table: {e}")


def convert_notify_to_str(notify=Notify):
    # Convert notify dictionary to ensure all values are strings
    notify = {k: str(v) for k, v in notify.items()}


def convert_to_original_type(notify_as_str: str):
    return {Notify(key): value.lower() == 'true' if isinstance(value, str) else value for key, value in notify_as_str.items()}


def get_member_by_name(member_list, name):
    # Get the first Member object from the list with the given name.5
    for member in member_list:
        if member.name == name:
            m = Member(name)
            m.notify = convert_to_original_type(member.notify)
            return m
    return None  # Return None if no member with the specified name is found


def get_notify_by_member_name(member_list, name):
    # Get the first Member object from the list with the given name.5
    for member in member_list:
        if member.name == name:
            member.notify = convert_to_original_type(member.notify)
            return member.notify
    return None  # Return None if no member with the specified name is found


# def print_member_params(member_list):
#     for member in member_list:
#         if isinstance(member, Member):
#             print(f"Name: {member.name}")
#             print("Notify:")
#             for key, value in member.notify.items():
#                 print(f"    {key}: {value}")
#             print()
