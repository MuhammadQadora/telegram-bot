from local_user_DB import *

list_members = []
msgchatid = 123

if is_member_in_list_by_name(list_members, msgchatid):
    member = get_member_by_name(list_members, msgchatid)
    notify = member.notify
    # Setting all notifications to False
    for notification in Notify:
        notify[notification] = False
else:
    add_member(list_members, msgchatid)

print(len(list_members))

# Example lists containing Member objects
list1 = [Member("Alice"), Member("Bob")]
list2 = [Member("Charlie"), "Not a Member", Member("David")]

# Function to print all parameters of Member objects in a list
def print_member_params(member_list):
    for member in member_list:
        if isinstance(member, Member):
            print(f"Name: {member.name}")
            print("Notify:")
            for key, value in member.notify.items():
                print(f"    {key}: {value}")
            print()

# Print all parameters of Member objects in the example lists
print("Printing parameters for list1:")
print_member_params(list1)

print("Printing parameters for list2:")
print_member_params(list2)