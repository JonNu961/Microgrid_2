import json

def create_message(performative, sender, receiver, content):
    return json.dumps({
        "performative": performative,
        "sender": sender,
        "receiver": receiver,
        "content": content
    })

def parse_message(message_str):
    return json.loads(message_str)
