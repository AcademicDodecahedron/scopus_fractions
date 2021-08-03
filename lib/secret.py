# (c) E-kvadrat Consulting & Media, 2021

from pathlib import Path
import json

def get_nonempty_field_or_error(json_dict: dict, json_path, field_name: str):
    if field_name not in json_dict:
        print(field_name, 'not in', json_path)
        exit(1)
    value = json_dict[field_name]
    if value is None or value == '':
        print(field_name, 'is empty in', json_path)
        exit(1)
    return value

def load_secrets(json_path):
    try:
        with open(json_path) as json_file:
            json_dict = json.load(json_file)
            api_key = get_nonempty_field_or_error(json_dict, json_path, 'ApiKey')
            inst_token = get_nonempty_field_or_error(json_dict, json_path, 'InstToken')
            return api_key, inst_token
    except IOError:
        print(json_path, 'file not found')
        exit(1)
