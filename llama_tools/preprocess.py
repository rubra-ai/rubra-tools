from typing import List
import json


TOOL_SYSTEM_PROMPT_RUBRA = (
    "You have access to the following tools: {tool_text}\n"
    "You can choose to respond with one or more tool calls at once, or with a chat message back to the user. "
    "Ensure you have all necessary details before making tool calls. If additional information is needed, "
    "ask the user appropriately. Any tool call you make must correspond to the functions listed above.\n"
    "If you decide to call tools, format your response in JSONL. Start with the keyword `<functions>` followed by the JSON object:\n"
    '`<functions>{{"name": "<function_name>", "arguments": {{"<arg1_name>": "<arg1_value>", "<arg2_name>": "<arg2_value>", ...}}}}`'
)

def json_schema_to_typescript_type(schema, param_name):
    ts_type = "any"  # default type
    enum_comment = ""
    integer_comment = ""
    description_comment = ""

    if isinstance(schema, dict) and "type" in schema:
        json_type = schema["type"]
        if json_type == "array":
            item_type = (
                "any"
                if "items" not in schema
                else json_schema_to_typescript_type(schema["items"], param_name)[0]
            )
            ts_type = f"{item_type}[]"
        elif json_type == "number":
            ts_type = "number"
        elif json_type == "integer":
            ts_type = (
                "number"  # TypeScript doesn't differentiate between number and integer
            )
            integer_comment = f" * @param {param_name} - Integer"
        elif json_type == "object":
            ts_type, _ = generate_typescript_interface(schema, param_name)
        elif json_type == "boolean":
            ts_type = "boolean"
        elif json_type == "null":
            ts_type = "null"
        elif json_type == "string":
            ts_type = "string"

    if "enum" in schema:
        enum_comment = f" * @enum {param_name} - Possible values: " + ", ".join(
            [f'"{enum_value}"' for enum_value in schema["enum"]]
        )
        ts_type = "string"
    if "description" in schema:
        description_comment = f' * @param {param_name} - {schema["description"]}'

    # Return only the type for nested objects to avoid duplicating comments
    if isinstance(schema, dict) and schema.get("type") == "object":
        return ts_type, "", "", ""

    return ts_type, enum_comment, integer_comment, description_comment


def generate_typescript_interface(schema, interface_name):
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    interface_body = []
    descriptions = []
    for prop_name, prop_schema in properties.items():
        prop_type, enum_comment, integer_comment, description_comment = (
            json_schema_to_typescript_type(prop_schema, prop_name)
        )
        is_optional = prop_name not in required
        interface_body.append(
            f'    {prop_name}{"?" if is_optional else ""}: {prop_type};'
        )
        if description_comment:
            descriptions.append(description_comment)
        if enum_comment:
            descriptions.append(enum_comment)
        if integer_comment:
            descriptions.append(integer_comment)

    comments = "\n".join(descriptions)
    interface_definition = (
        f"interface {interface_name} {{\n" + "\n".join(interface_body) + "\n}"
    )
    return interface_definition, comments


def convert_parameters_list_to_dict(parameters):
    properties = {}
    required = []
    for param in parameters:
        properties[param["name"]] = param
        if "default" not in param:
            required.append(param["name"])
    return {"properties": properties, "required": required}


def generate_typescript_function(function_schema) -> str:
    func_name = function_schema["name"]
    description = function_schema.get("description", "")

    # Check if parameters is a list and convert if necessary
    parameters_info = function_schema.get("parameters", {})
    if isinstance(parameters_info, list):
        parameters_info = convert_parameters_list_to_dict(parameters_info)

    parameters_schema = parameters_info.get("properties", {})
    required_params = parameters_info.get("required", [])

    args_list = []
    comments_list = []
    interfaces = []
    for param_name, param_schema in parameters_schema.items():
        ts_type, enum_comment, integer_comment, description_comment = (
            json_schema_to_typescript_type(param_schema, param_name)
        )
        if ts_type.startswith("interface"):
            interface_definition, nested_comments = generate_typescript_interface(
                param_schema, f"{func_name}_{param_name.capitalize()}Params"
            )
            interfaces.append(interface_definition)
            comments_list.append(nested_comments)
            ts_type = f"{func_name}_{param_name.capitalize()}Params"
        else:
            if description_comment:
                comments_list.append(description_comment)
            if enum_comment:
                comments_list.append(enum_comment)
            if integer_comment:
                comments_list.append(integer_comment)
        is_optional = param_name not in required_params
        args_list.append(f'{param_name}{"?" if is_optional else ""}: {ts_type}')

    args_str = ", ".join(args_list)
    comments_str = "\n".join(comments_list)
    interfaces_str = "\n\n".join(interfaces)

    description_comment = f" * {description}\n" if description else ""
    typescript_func_declaration = (
        "/**\n"
        + description_comment
        + (comments_str + "\n" if comments_str else "")
        + " */\n"
        + (interfaces_str + "\n\n" if interfaces_str else "")
        + f"function {func_name}({args_str}): any {{}}"
    )

    return typescript_func_declaration



def format_tools(tools: List[dict]) -> str:
    func_defs = []
    for t in tools:
        tool_schema = t["function"] if "function" in t else t
        func_defs.append(generate_typescript_function(tool_schema))
    
    typescript_functions_str = "\n\n".join(func_defs)
    res = TOOL_SYSTEM_PROMPT_RUBRA.format(tool_text=typescript_functions_str)
    return res



def preprocess_input(msgs: List[dict], tools: List[dict]):
    tool_system_prompt = format_tools(tools)
    processed_msgs = process_messages(msgs, tool_system_prompt)
    return processed_msgs


def process_messages(messages: List[dict], function_str: str):
    func_observation_map = {}
    processed_msg = []

    for i in range(len(messages)):
        if messages[i]["role"] != "tool" and len(func_observation_map) > 0:
            # Insert the observation from the tool call before the next message
            func_observation_array = list(func_observation_map.values())
            observation_str = "<<observation>>" + json.dumps(func_observation_array)
            observation_call = {"role": "observation", "content": observation_str}
            processed_msg.append(observation_call)
            func_observation_map.clear()

        if i == 0:
            if messages[0]["role"] == "system":
                old_content = messages[0]["content"]
                sys_msg = {"role": "system", "content": old_content + "\n" + function_str}
                processed_msg.append(sys_msg)
            else:
                # Insert a system message of tool definition before the first message
                sys_msg = {"role": "system", "content": "You are a helpful assistant.\n" + function_str}
                processed_msg.append(sys_msg)
                processed_msg.append(messages[0]) # first message is always either system or user msg

        elif messages[i]["role"] == "assistant" and "tool_calls" in messages[i]:
            # Convert OpenAI function call format to Rubra format
            tool_call_str = construct_tool_call_str(messages[i]["tool_calls"], func_observation_map)
            function_call = {"role": "function", "content": tool_call_str}
            processed_msg.append(function_call)

        elif messages[i]["role"] == "tool":
            tool_call_id = messages[i]["tool_call_id"]
            if tool_call_id in func_observation_map:
                func_observation_map[tool_call_id] = messages[i]["content"]
            else:
                print(f"Tool call id not found in the map: {tool_call_id}")
                # TODO: the input is not valid in this case, should return an error

        else:
            processed_msg.append(messages[i])

    if len(func_observation_map) > 0:
        # Insert the observation from the tool call before the next message
        func_observation_array = list(func_observation_map.values())
        observation_str = "<<observation>>" + json.dumps(func_observation_array)
        observation_call = {"role": "observation", "content": observation_str}
        processed_msg.append(observation_call)
        func_observation_map.clear()

    return processed_msg


def construct_tool_call_str(tool_calls, func_observation_map) -> str:
    tool_list = []
    for tool_call in tool_calls:
        tool_call_id = tool_call["id"]
        func_observation_map[tool_call_id] = ""  # Initialize with empty value, updated later from the message with tool role
        
        tool_list.append(json.dumps(tool_call["function"]))

    # Converting the Python dictionary to a YAML formatted string
    tool_call_str = "<functions>" + "\n".join(tool_list)
    return tool_call_str


if __name__ == "__main__":
    tools = [{"type": "function","function":{"name":"calculate_distance","description":"Calculate the distance between two locations","parameters":{"type":"object","properties":{"origin":{"type":"string","description":"The starting location"},"destination":{"type":"string","description":"The destination location"},"mode":{"type":"string","description":"The mode of transportation"}},"required":["origin","destination","mode"]}}},{"type": "function","function":{"name":"generate_password","description":"Generate a random password","parameters":{"type":"object","properties":{"length":{"type":"integer","description":"The length of the password"}},"required":["length"]}}}]
    msgs = [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': 'What is the distance between San Francisco and Cupertino by driving and by air from both directions?'}, {'role': 'assistant', 'tool_calls': [{'id': '0', 'function': {'name': 'calculate_distance', 'arguments': '{"origin":"San \nFrancisco","destination":"Cupertino","mode":"drive"}'}, 'type': 'function'},{'id': '1', 'function': {'name': 'calculate_distance', 'arguments': '{"origin":"San \nFrancisco","destination":"Cupertino","mode":"air"}'}, 'type': 'function'}]}, {'role': 'tool', 'tool_call_id': '0', 'name': 'calculate_distance', 'content': 'Distance is 50 miles.'}, {'role': 'tool', 'tool_call_id': '1', 'name': 'calculate_distance', 'content': 'Distance  by air is 50 miles.'}]
    new_msgs = preprocess_input(msgs, tools)
    print(json.dumps(new_msgs, indent=2))
    