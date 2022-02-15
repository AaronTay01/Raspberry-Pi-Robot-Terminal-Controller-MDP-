import json

def format_for(target, payload):
    return json.dumps({
        'target': target,
        'payload': payload
    })