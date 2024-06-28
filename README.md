# rubra-tools

## prerequisites
pip install rubra-tools:
```
pip install rubra_tools
```

Use npm to install package `jsonrepair` to help fix some rare edgecases.
```
npm install jsonrepair
```

## Use rubra-tools with transformer lib
1. load a rubra function calling model:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "rubra-ai/Llama-3-8b-function-calling-alpha-v1"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
```

2. define functions:
```python
functions = [
    {
            'type': 'function',
            'function': {
                'name': 'addition',
                'description': "Adds two numbers together",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'a': {
                            'description': 'First number to add',
                            'type': 'string'
                        },
                        'b': {
                            'description': 'Second number to add',
                            'type': 'string'
                        }
                    },
                    'required': []
                }
            }
        },
        {
            'type': 'function',
            'function': {
                'name': 'subtraction',
                'description': "Subtracts two numbers",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'a': {
                            'description': 'First number to be subtracted from',
                            'type': 'string'
                        },
                        'b': {
                            'description': 'Number to subtract',
                            'type': 'string'
                        }
                    },
                    'required': []
                }
            }
        },
        {
            'type': 'function',
            'function': {
                'name': 'multiplication',
                'description': "Multiply two numbers together",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'a': {
                            'description': 'First number to multiply',
                            'type': 'string'
                        },
                        'b': {
                            'description': 'Second number to multiply',
                            'type': 'string'
                        }
                    },
                    'required': []
                }
            }
        },
        {
            'type': 'function',
            'function': {
                'name': 'division',
                'description': "Divide two numbers",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'a': {
                            'description': 'First number to use as the dividend',
                            'type': 'string'
                        },
                        'b': {
                            'description': 'Second number to use as the divisor',
                            'type': 'string'
                        }
                    },
                    'required': []
                }
            }
        },
]
```

3. Start the conversation with a simple math chaining question:
```python
from rubra_tools import preprocess_input, postprocess_output

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the result of four plus six? Take the result and add 2? Then multiply by 5 and then divide by two"},
]

def run_model(messages, functions):
    ## Format messages in Rubra's format
    formatted_msgs = preprocess_input(msgs=messages, tools=functions)

    input_ids = tokenizer.apply_chat_template(
        formatted_msgs,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    terminators = [
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    outputs = model.generate(
        input_ids,
        max_new_tokens=1000,
        eos_token_id=terminators,
        do_sample=True,
        temperature=0.1,
        top_p=0.9,
    )
    response = outputs[0][input_ids.shape[-1]:]
    raw_output = tokenizer.decode(response, skip_special_tokens=True)
    return raw_output

raw_output = run_model(messages, functions)
# Check if there's a function call
function_call = postprocess_output(raw_output)
if function_call:
    print(function_call)
else:
    print(raw_output)
```

You should see this output, which is a function call made by the ai assistant:
```
[{'id': 'fc65a533', 'function': {'name': 'addition', 'arguments': '{"a": "4", "b": "6"}'}, 'type': 'function'}]
```


4. continue the conversation by provide the function call result:
```python
if function_call:
    # append the assistant tool call msg
    messages.append({"role": "assistant", "tool_calls": function_call})
    # append the result of the tool call in openai format, in this case, the value of add 6 to 4 is 10.
    messages.append({'role': 'tool', 'tool_call_id': function_call[0]["id"], 'name': function_call[0]["function"]["name"], 'content': '10'})
    raw_output = run_model(messages, functions)
    # Check if there's a function call
    function_call = postprocess_output(raw_output)
    if function_call:
        print(function_call)
    else:
        print(raw_output)
```

The AI will make another call
```
[{'id': '2ffc3de4', 'function': {'name': 'addition', 'arguments': '{"a": "10", "b": "2"}'}, 'type': 'function'}]
```

5. keep going...

You can also find all the code above in `transformer.ipynb`.

## build and publish
1. install flit
```
pip install flit
```

2. build the dist
```
flit build
```

3. push the dist, you might need to change the version number in __init__.py. 
You would also need pypi account and api token ready.
```
flit publish
```

this might help --
create `~/.pypirc` with:
```
[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = <your-api-token-starts-with-pypi->
```
