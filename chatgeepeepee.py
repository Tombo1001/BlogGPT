import openai
import threading
import re
import os
from datetime import datetime
from dotenv import load_dotenv

# Configure your OpenAI API key
load_dotenv()
openai.api_key = os.environ.get('API_KEY')

# Create a lock to synchronize access to the OpenAI API
api_lock = threading.Lock()

def generate_chat_response(prompt):
    with api_lock:
        response = openai.ChatCompletion.create( #using gpt-3.5-turbo model
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

    chat_result = response.choices[0].message
    tokens_used = response.usage.total_tokens
    print("Tokens used:", tokens_used)
    return chat_result

def format_result_as_md(result):
    return f"\n{result['content']}\n---"

# Read prompts from a Markdown file; build a prompts list
input_file = 'prompts.md'
prompts = []

with open(input_file, 'r') as file:
    ml_string = ""
    for line in file:
        if re.search(r'^(?!\s+)[-•*] (.+)', line, flags=re.MULTILINE):
            if ml_string:
                prompts.append(ml_string)
                ml_string = line
            else:
                ml_string = line
        elif re.search(r'^(?:(?!\n$)\s{2,}[^\n]+)$', line, flags=re.MULTILINE):
            ml_string += line
    prompts.append(ml_string) # append when all line are read

# Create a list to hold the generated responses
responses = []

def worker_thread(prompt):
    print(prompt)
    chat_response = generate_chat_response(prompt)
    formatted_md = format_result_as_md(chat_response)

    # Append the formatted response to the list
    responses.append(formatted_md)

# Create and start multiple worker threads
for prompt in prompts:
    prompt = f"Write an SEO optimised blog post in markdown which is based on the following bullet points:\n{prompt}"
    worker_thread(prompt)

# Write responses to a Markdown file
for response in responses:
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y_%m_%d-%H_%M")
    output_file = f'{formatted_datetime}-generated_responses.md'
    with open(output_file, 'w') as file:
        file.write(response + '\n')