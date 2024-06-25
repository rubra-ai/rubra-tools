import json
import uuid
import re
from typing import List
import pythonmonkey
import re

# Assuming jsonrepair is accessible
jsonrepair = pythonmonkey.require('jsonrepair').jsonrepair

def clean_command_string(command_str):
    cleaned_command = re.sub(r'\\(?!["\\/bfnrt]|u[a-fA-F0-9]{4})', '', command_str)
    cleaned_command = cleaned_command.replace('\\"', '"')
    if cleaned_command.startswith('"') and cleaned_command.endswith('"'):
        cleaned_command = cleaned_command[1:-1]
    return cleaned_command

def parse_json_safely(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            repaired = jsonrepair(json_str)
            return json.loads(repaired)
        except Exception:
            return json_str

def clean_json_object(obj):
    if isinstance(obj, dict):
        return {k: clean_json_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_object(item) for item in obj]
    elif isinstance(obj, str):
        cleaned = clean_command_string(obj)
        return parse_json_safely(cleaned) if cleaned.startswith('{') or cleaned.startswith('[') else cleaned
    else:
        return obj

def extract_tool_calls(output_str):
    pattern = r'starttoolcall(.*?)endtoolcall'
    matches = re.findall(pattern, output_str, re.DOTALL)
    return matches

def postprocess_output(output_str: str) -> List[dict]:
    tool_calls = extract_tool_calls(output_str)
    
    function_call_json = []
    for call in tool_calls:
        try:
            parsed_call = parse_json_safely(call)
            cleaned_call = clean_json_object(parsed_call)
            
            if isinstance(cleaned_call.get('arguments'), dict):
                cleaned_call['arguments'] = json.dumps(cleaned_call['arguments'])
            
            function_call_json.append(cleaned_call)
        except Exception as e:
            print(f"Error processing function call: {e}")
    
    res = []
    for fc in function_call_json:
        res.append({
            "id": uuid.uuid4().hex[:8],
            "function": fc,
            "type": "function",
        })
    
    return res

if __name__ == "__main__":
    # Test the function with a sample input
    output_str = '''Some text before starttoolcall{"name": "funcA", "arguments": {"param1": 1}endtoolcall
    More text starttoolcall{"name": "funcB", "arguments": {"param2": "test"}}endtoolcall'''
    
    parsed_json = postprocess_output(output_str)
    if parsed_json:
        print(json.dumps(parsed_json, indent=2))
    else :
        print(output_str)
