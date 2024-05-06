import json
import uuid
from typing import List

def postprocess_output(output_str: str) -> List[dict]:
    if not output_str.lstrip().startswith("<<functions>>"):
        return []
    str_to_parse = output_str.split("<<functions>>")[1]
    try:
        function_call_json = json.loads(str_to_parse)
    except:
        return []
    res = []
    for fc in function_call_json:
        res.append({
            "id": uuid.uuid4().hex[:8],
            "function": fc,
            "type": "function",
        })
    return res

if __name__ == "__main__":
    output_str = "<<functions>>[{\"name\": \"calculate_distance\", \"arguments\": \"{\\\"origin\\\":\\\"San Francisco\\\",\\\"destination\\\":\\\"Cupertino\\\",\\\"mode\\\":\\\"drive\\\"}\"}]"
    parsed_json = postprocess_output(output_str)
    if parsed_json:
        print(parsed_json)
    else :
        print(output_str)