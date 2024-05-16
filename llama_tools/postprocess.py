import json
import uuid
from typing import List
import pythonmonkey
import re

jsonrepair = pythonmonkey.require('jsonrepair').jsonrepair


import json
import pythonmonkey
import re

# Assuming jsonrepair is accessible
jsonrepair = pythonmonkey.require('jsonrepair').jsonrepair

def parse_if_json(value):
    # print(f"Parsing value: {value}")
    try:
        value = jsonrepair(value)
        return json.loads(value)
    except Exception as e:
        try:
            return json.loads(value)
        except ValueError:
            return value

def clean_command_string(command_str):
    # Use regex to remove unwanted backslashes except those needed for actual escape sequences
    cleaned_command = re.sub(r'\\(?!["\\/bfnrt]|u[a-fA-F0-9]{4})', '', command_str)
    # Correctly handle escaped double quotes
    cleaned_command = cleaned_command.replace('\\"', '"')
    # Remove surrounding quotes if present
    if cleaned_command.startswith('"') and cleaned_command.endswith('"'):
        cleaned_command = cleaned_command[1:-1]
    return cleaned_command

def clean_json_strings(input_str):
    # print(f"RAW string input: {input_str}\n")
    try:
        # Use jsonrepair to fix the JSON and load it
        repaired_json = jsonrepair(input_str)
        data = json.loads(repaired_json)
        # Check each item and parse if it's a JSON-formatted string
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    # Attempt to parse the string value as JSON if it seems like JSON
                    if value.startswith('{') or value.startswith('['):
                        data[key] = parse_if_json(value)
                    else:
                        # Otherwise, use the specific cleaning logic for command-like strings
                        data[key] = clean_command_string(value)
                elif isinstance(value, dict):
                    # Recursively clean any nested dictionaries
                    data[key] = {k: clean_command_string(v) if isinstance(v, str) else v for k, v in value.items()}

        # Return the modified data structure, not as a JSON string but as a dictionary
        return data

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None



def postprocess_output(output_str: str) -> List[dict]:
    if output_str.lstrip().startswith("<functions>"):
        str_to_parse = output_str.split("<functions>")[1]
    elif output_str.lstrip().startswith("functions>"):
        str_to_parse = output_str.split("functions>")[1]
    else:
        return []
    
    # list_of_str_to_parse = str_to_parse.splitlines() # TODO: need better way to handle jsonl format
    list_of_str_to_parse = str_to_parse.split("\n")
    function_call_json = []
    try: # every function call has to be valid json
        for l in list_of_str_to_parse:
            fc = clean_json_strings(l)
                
            if type(fc["arguments"]) != str:
                fc["arguments"] = json.dumps(fc["arguments"])
            function_call_json.append(fc)
    except Exception as e:
        print(f"Error : {e}")
        
    res = []
    for fc in function_call_json:
        res.append({
            "id": uuid.uuid4().hex[:8],
            "function": fc,
            "type": "function",
        })
    return res

if __name__ == "__main__":
    output_str = "<functions>{\"name\": \"calculate_distance\", \"arguments\": \"{\\\"origin\\\":\\\"San \\nFrancisco\\\",\\\"destination\\\":\\\"Cupertino\\\",\\\"mode\\\":\\\"drive\\\"}\"}\n{\"name\": \"calculate_distance\", \"arguments\": \"{\\\"origin\\\":\\\"San \\nFrancisco\\\",\\\"destination\\\":\\\"Cupertino\\\",\\\"mode\\\":\\\"air\\\"}\"}"
    # output_str = '<functions>{"name": "calculate_distance", "arguments": {"origin": "San Francisco", "destination": "Cupertino", "mode": "driving"}}\n{"name": "calculate_distance", "arguments": {"origin": "San Francisco", "destination": "Cupertino", "mode": "air"}}'
    # output_str = ' <functions>{"name": "write", "arguments": "{\\"content\\":\\"# Sample *.gpt Files\\\\n\\\\n## add-go-mod-dep.gpt\\\\nLink to add-go-mod-dep.gpt\\rn\\\\n## bob-as-shell.gpt\\\\nLink to bob-as-shell.gpt\\rn\\\\n## bob.gpt\\\\nLink to bob.gpt\\rn\\\\n## car-notifier/car-notifier.gpt\\\\nLink to car-notifier/car-notifier.gpt\\rn\\\\n## count-lines-of-code.gpt\\\\nLink to count-lines-of-code.gpt\\rn\\\\n## describe-code.gpt\\\\nLink to describe-code.gpt\\rn\\\\n## echo.gpt\\\\nLink to echo.gpt\\rn\\\\n## fac.gpt\\\\nLink to fac.gpt\\rn\\\\n## git-commit.gpt\\\\nLink to git-commit.gpt\\rn\\\\n## hacker-news-headlines.gpt\\\\nLink to hacker-news-headlines.gpt\\rn\\\\n## hamlet-summarizer/hamlet-summarizer.gpt\\\\nLink to hamlet-summarizer/hamlet-summarizer.gpt\\rn\\\\n## helloworld.gpt\\\\nLink to helloworld.gpt\\rn\\\\n## recipegenerator/recipegenerator.gpt\\\\nLink to recipegenerator/recipegenerator.gpt\\rn\\\\n## samples-readme.gpt\\\\nLink to samples-readme.gpt\\rn\\\\n## search.gpt\\\\nLink to search.gpt\\rn\\\\n## sentiments.gpt\\\\nLink to sentiments.gpt\\rn\\\\n## sqlite-download.gpt\\\\nLink to sqlite-download.gpt\\rn\\\\n## syntax-from-code.gpt\\\\nLink to syntax-from-code.gpt\\rn\\\\n## time.gpt\\\\nLink to time.gpt\\rn\\\\n## treasure-hunt/treasure-hunt.gpt\\\\nLink to treasure-hunt/treasure-hunt.gpt\\\\n\\\\nThis document provides a summary of each sample *.gpt file located in the examples/ directory. Each entry includes a link to the referenced file.\\\\n\\",\\"filename\\":\\"examples/README.md\\"}"}'
    parsed_json = postprocess_output(output_str)
    if parsed_json:
        print(f"PARSED_JSON type: {type(parsed_json)}")
        print(parsed_json)
    else :
        print(output_str)