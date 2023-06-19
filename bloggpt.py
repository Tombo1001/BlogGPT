import openai
import threading
import re
import os
from datetime import datetime
from dotenv import load_dotenv

class ChatBot:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.environ.get('API_KEY')
        self.api_lock = threading.Lock()
        self.prompts = []
        self.responses = []

    def generate_chat_response(self, prompt):
        with self.api_lock:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        chat_result = response.choices[0].message
        tokens_used = response.usage.total_tokens
        print("Tokens used:", tokens_used)
        return chat_result

    def format_result_as_md(self, result):
        return f"\n{result['content']}\n---"

    def read_prompts_from_file(self, input_file):
        with open(input_file, 'r') as file:
            ml_string = ""
            for line in file:
                if re.search(r'^(?!\s+)[-•*] (.+)', line, flags=re.MULTILINE):
                    if ml_string:
                        self.prompts.append(ml_string)
                        ml_string = line
                    else:
                        ml_string = line
                elif re.search(r'^(?:(?!\n$)\s{2,}[^\n]+)$', line, flags=re.MULTILINE):
                    ml_string += line
            self.prompts.append(ml_string)

    def worker_thread(self, prompt):
        print(prompt)
        chat_response = self.generate_chat_response(prompt)
        formatted_md = self.format_result_as_md(chat_response)
        self.responses.append(formatted_md)

    def generate_responses(self, input_file):
        self.read_prompts_from_file(input_file)
        for prompt in self.prompts:
            prompt = f"Write an SEO optimised blog post in markdown which is based on the following bullet points:\n{prompt}"
            self.worker_thread(prompt)

    def write_responses_to_file(self):
        for response in self.responses:
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime("%Y_%m_%d-%H_%M")
            output_file = f'{formatted_datetime}-generated_responses.md'
            with open(output_file, 'w') as file:
                file.write(response + '\n')

if __name__ == '__main__':
    # Create an instance of the ChatBot class
    bot = ChatBot()

    # Generate and write responses to file
    bot.generate_responses('prompts.md')
    bot.write_responses_to_file()
