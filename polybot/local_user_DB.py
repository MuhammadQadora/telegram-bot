from enum import Enum

class Notify(Enum):
    ISPHOTO = 'isPhoto'
    SENTPHOTO = 'sentPhoto'
    ISGPT = 'isGPT'
    CHATWITHGPT = 'chatWithGPT'
    TEXTTOIMAGE = 'textToImage'

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
    #Check if a member object with a given name exists in the list.
    return any(member.name == name for member in bot_members)

def add_member(bot_members, name):
    #Add a new member to the list if it doesn't already exist.
    if is_member_in_list_by_name(bot_members, name) == False:
        bot_members.append(Member(name))

def get_member_by_name(member_list, name):
    #Get the first Member object from the list with the given name.5
    for member in member_list:
        if member.name == name:
            return member
    return None  # Return None if no member with the specified name is found

def get_notify_by_member_name(member_list, name):
    #Get the first Member object from the list with the given name.5
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