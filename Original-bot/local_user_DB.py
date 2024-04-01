from enum import Enum
from loguru import logger
class Notify(Enum):
    CHATGPT = 'chatgpt'
    GPT4 = 'gpt4'
    YOLO = 'yolo'
    QUESTION = 'question'
    TEXT_TO_IMAGE = 'textToImage'

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


def is_member_in_list_by_name(bot_members, name):
    """
    Check if a member object with a given name exists in the list.
    """
    result = [i for i in bot_members if name in i]
    logger.info(result)
    if result:
        return True
    else:
        return False

def add_member(bot_members, name):
    """
    Add a new member to the list if it doesn't already exist.
    """
    res = is_member_in_list_by_name(bot_members, name)
    logger.info(res)
    if is_member_in_list_by_name(bot_members, name) == False:
        print('insideeeeeee')
        bot_members.append(Member(name))
        print('passed bot_members')
        print(len(bot_members))

def get_member_by_name(member_list, name):
    """
    Get the first Member object from the list with the given name.5
    """
    for member in member_list:
        if member.name == name:
            return member
    return None  # Return None if no member with the specified name is found

def get_notify_by_member_name(member_list, name):
    """
    Get the first Member object from the list with the given name.5
    """
    for member in member_list:
        if member.name == name:
            return member.notify
    return None  # Return None if no member with the specified name is found

