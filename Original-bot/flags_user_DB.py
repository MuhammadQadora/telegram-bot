from enum import Enum
from loguru import logger
import os
import boto3

dynamodb = boto3.resource('dynamodb', region_name=os.environ["REGION_NAME"])
table = dynamodb.Table(os.environ["FLAGS_TABLE_NAME"])

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
    try:
        response = table.update_item(
            Key={'name': name},
            UpdateExpression="SET notify = :notify_updates",
            ExpressionAttributeValues={
                ':notify_updates': notify_updates
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"Update succeeded: {response}")
    except Exception as e:
        print(f"Error updating item: {e}")

def is_member_in_list_by_name(bot_members, name):
    # Check if a member object with a given name exists in the list.
    return any(member.name == name for member in bot_members)


def add_member(bot_members, name):
    # Add a new member to the list if it doesn't already exist
    if not is_member_in_list_by_name(bot_members, name):
        new_member = Member(name)
        bot_members.append(new_member)
        
        # # Convert notify dictionary to ensure all values are strings
        # notify_as_str = {k: str(v) for k, v in new_member.notify.items()}

        
        # Add the new member to the DynamoDB table
        item = {
            '_id': new_member.name,
            'name': new_member.name,
            'notify': str(new_member.notify)
        }
        try:
            table.put_item(Item=item)
            logger.info(f"Added {name} to DynamoDB table.")
        except Exception as e:
            logger.error(f"Error adding {name} to DynamoDB table: {e}")

def convert_notify_to_str(notify = Notify):
    # Convert notify dictionary to ensure all values are strings
    notify = {k: str(v) for k, v in notify.items()}

def convert_to_original_type(notify_as_str):
    return {Notify(key): value for key, value in notify_as_str.items()}

def get_member_by_name(member_list, name):
    # Get the first Member object from the list with the given name.5
    for member in member_list:
        if member.name == name:
            return member
    return None  # Return None if no member with the specified name is found


def get_notify_by_member_name(member_list, name):
    # Get the first Member object from the list with the given name.5
    for member in member_list:
        if member.name == name:
            return member.notify
    return None  # Return None if no member with the specified name is found


def print_member_params(member_list):
    for member in member_list:
        if isinstance(member, Member):
            print(f"Name: {member.name}")
            print("Notify:")
            for key, value in member.notify.items():
                print(f"    {key}: {value}")
            print()
