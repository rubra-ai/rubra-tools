import json
import uuid
from typing import List

def postprocess_output(output_str: str) -> List[dict]:
    if not output_str.lstrip().startswith("<functions>"):
        return []
    str_to_parse = output_str.split("<functions>")[1]
    list_of_str_to_parse = str_to_parse.splitlines()
    function_call_json = []
    try: # every function call has to be valid json
        for l in list_of_str_to_parse:
            function_call_json.append(json.loads(l))
    except Exception as e:
        print(e)
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
    parsed_json = postprocess_output(output_str)
    if parsed_json:
        print(f"PARSED_JSON type: {type(parsed_json)}")
        print(parsed_json)
    else :
        print(output_str)