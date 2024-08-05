import json
import logging
import os
import importlib
import traceback
from datetime import datetime
import sys

import pkg_resources

def load_prompt_file(filename):
    """Loads a text file from the installed package data."""
    resource_package = __name__  # name of the package where this module is located
    resource_path = f'prompts/{filename}'  # Do not use os.path.join() here
    return pkg_resources.resource_string(resource_package, resource_path).decode('utf-8')

from tests import test_method_logic

from src.gemini_api import GeminiAPI

# Retrieve API key and project ID from environment variables
gemini_api_key = os.getenv('GEMINI_API_KEY')
project_id = os.getenv('GEMINI_PROJECT_ID')

# Initialize GeminiAPI instance
gemini = GeminiAPI(api_key=gemini_api_key, project_id=project_id)

class LlmAnswerGenerator:
    def __init__(self, model='gemini-pro'):
        self.gemini = gemini
        self.model = model
        self.conversation_history = []

    def get_answer(self, prompt, stream=False):
        try:
            response = self.gemini.generate_content(text=prompt, model_id=self.model, stream=stream)
            return response
        except Exception as e:
            logging.error(f"Error in get_answer: {e}")
            return None

    def get_response(self, prompt):
        return self.get_answer(prompt)


class MyClass:
    def __init__(self, file_path):
        self.file_path = file_path

    def dynamic_method(self, retries=3):
        module_name = 'src.method_logic'
        method_name = 'method_logic'
        module = importlib.import_module(module_name)
        importlib.reload(module)
        method = getattr(module, method_name)

        for attempt in range(retries):
            try:
                result = method(self)
                self.validate_output(result)
                return result
            except Exception as e:
                logging.error(f"Error in method execution: {e}")
                corrected_code = self.correct_method_code(method_name, method, e)
                self.apply_corrected_method(module_name, method_name, corrected_code)
                method = getattr(module, method_name)

        raise RuntimeError("All correction attempts failed.")

    def validate_output(self, result):
        if 'path' not in result:
            raise ValueError("path key not present. Output validation failed.")

    def correct_method_code(self, method_name, method, error):
        current_code = self.get_method_code(method_name, method)
        prompt_template = self.read_prompt_template()
        prompt = prompt_template.format(current_code=current_code, error_details=str(error))
        generator = LlmAnswerGenerator()
        corrected_code = generator.get_response(prompt)
        return corrected_code

    def apply_corrected_method(self, module_name, method_name, corrected_code):
        method_logic_path = os.path.join(os.path.dirname(__file__), f'{module_name}.py')
        with open(method_logic_path, 'w') as file:
            file.write(corrected_code)
        importlib.reload(importlib.import_module(module_name))

    def get_method_code(self, method_name, method):
        import inspect
        return inspect.getsource(method)

    def read_prompt_template(self):
        return load_prompt_file("correction_prompt.txt")


def format_input_prompt(improve_prompt, current_method, last_result):
    separator = '=== SEPARATOR ==='
    before, after = improve_prompt.split(separator, 1)
    formatted_before = before.format(current_method, last_result)
    prompt = formatted_before + separator + after
    return prompt


def read_serialize_logic():
    serialize_logic_path = os.path.join(os.path.dirname(__file__), 'serialize_logic.txt')
    with open(serialize_logic_path, 'r') as file:
        code = file.read()
    return code

def write_serialize_logic(code):
    serialize_logic_path = os.path.join(os.path.dirname(__file__), 'serialize_logic.txt')
    with open(serialize_logic_path, 'w') as file:
        file.write(code)

def generate_corrected_serialize_logic(error, current_code):
    prompt = f"Method code:\n{current_code}\nError:\n{str(error)}\nCorrect the serialize function to handle the error without adding comments or additional text."
    generator = LlmAnswerGenerator()
    corrected_code = generator.get_response(prompt)
    return corrected_code

def dynamic_serialize(obj):
    code = read_serialize_logic()
    local_vars = {}
    exec(code, globals(), local_vars)
    serialize = local_vars['serialize']

    try:
        return serialize(obj)
    except Exception as e:
        print(f"Serialization error: {e}")
        error_details = traceback.format_exc()
        corrected_code = generate_corrected_serialize_logic(error_details, code)
        write_serialize_logic(corrected_code)
        exec(corrected_code, globals(), local_vars)
        serialize = local_vars['serialize']
        return serialize(obj)


def generate_improved_method(current_method, last_result, iteration):
    if iteration == 0:
        prompt_file = "first_prompt.txt"
    elif iteration == 1:
        prompt_file = "second_prompt.txt"
    else:
        prompt_file = "third_prompt.txt"

    improve_prompt = load_prompt_file(prompt_file)

    if 'text' in last_result:
        last_result.pop('text')

    last_result_serialized = json.dumps(last_result, default=dynamic_serialize, ensure_ascii=False)

    prompt = format_input_prompt(improve_prompt, current_method, last_result_serialized)

    logging.info(f"Prompt being sent to Gemini model:\n{prompt}")

    generator = LlmAnswerGenerator()
    improved_method = generator.get_response(prompt)
    return improved_method


def generate_context_info(text_content, file_name="", file_extension="", additional_info=""):
    context_prompt = load_prompt_file("context_prompt.txt")
    
    if text_content:
        prompt = context_prompt.format(text_content[:1000])
    else:
        prompt = f"File name: {file_name}\nFile extension: {file_extension}\nAdditional info: {additional_info}"
    
    logging.info(f"Context Prompt being sent to Gemini model:\n{prompt}")

    generator = LlmAnswerGenerator()
    context_info = generator.get_response(prompt)
    return context_info


def update_method_logic(new_code, file_path):
    method_logic_path = os.path.join(os.path.dirname(__file__), 'method_logic.py')

    with open(method_logic_path, 'r') as file:
        current_code = file.read()

    with open(method_logic_path, 'w') as file:
        file.write(new_code)

    instance = MyClass(file_path=file_path)

    test_passed = False
    try:
        importlib.reload(test_method_logic)
        test_passed = test_method_logic.test_method_logic(instance)
    except Exception as e:
        logging.error(f"Test raised an error: {e}")
        test_passed = False

    if test_passed:
        logging.info("Tests passed. Keeping the new method logic.")
    else:
        logging.info("Tests failed. Reverting to the previous method logic.")
        with open(method_logic_path, 'w') as file:
            file.write(current_code)



# # Gpt4AnswerGenerator Class
# import json
# import logging
# import os
# import importlib
# import traceback
# from datetime import datetime
# import sys

# import pkg_resources

# def load_prompt_file(filename):
#     """Loads a text file from the installed package data."""
#     resource_package = __name__  # name of the package where this module is located
#     resource_path = f'prompts/{filename}'  # Do not use os.path.join() here
#     return pkg_resources.resource_string(resource_package, resource_path).decode('utf-8')

# from tests import test_method_logic

# from src.gemini_api import GeminiAPI

# gemini_api_key = os.getenv('GEMINI_API_KEY')
# project_id = os.getenv('GEMINI_PROJECT_ID')  # Get project_id from environment variables

# # Initialize GeminiAPI instance
# gemini = GeminiAPI(api_key=gemini_api_key, project_id=project_id)

# class LlmAnswerGenerator:
#     def __init__(self, model='gemini-pro'):
#         self.gemini = gemini
#         self.model = model
#         self.conversation_history = []

#     def get_answer(self, prompt, stream=False):
#         try:
#             response = self.gemini.generate_content(text=prompt, model_id=self.model, stream=stream)
#             return response
#         except Exception as e:
#             logging.error(f"Error in get_answer: {e}")
#             return None

#     def get_response(self, prompt):
#         return self.get_answer(prompt)



# class MyClass:
#     def __init__(self, file_path):
#         self.file_path = file_path

#     def dynamic_method(self, retries=3):
#         module_name = 'src.method_logic'
#         method_name = 'method_logic'
#         module = importlib.import_module(module_name)
#         importlib.reload(module)
#         method = getattr(module, method_name)

#         for attempt in range(retries):
#             try:
#                 result = method(self)
#                 self.validate_output(result)
#                 return result
#             except Exception as e:
#                 logging.error(f"Error in method execution: {e}")
#                 corrected_code = self.correct_method_code(method_name, method, e)
#                 self.apply_corrected_method(module_name, method_name, corrected_code)
#                 method = getattr(module, method_name)

#         raise RuntimeError("All correction attempts failed.")

#     def validate_output(self, result):
#         if 'path' not in result:
#             raise ValueError("path key not present. Output validation failed.")

#     def correct_method_code(self, method_name, method, error):
#         current_code = self.get_method_code(method_name, method)
#         prompt_template = self.read_prompt_template()
#         prompt = prompt_template.format(current_code=current_code, error_details=str(error))
#         generator = LlmAnswerGenerator()
#         corrected_code = generator.get_response(prompt)
#         return corrected_code

#     def apply_corrected_method(self, module_name, method_name, corrected_code):
#         method_logic_path = os.path.join(os.path.dirname(__file__), f'{module_name}.py')
#         with open(method_logic_path, 'w') as file:
#             file.write(corrected_code)
#         importlib.reload(importlib.import_module(module_name))

#     def get_method_code(self, method_name, method):
#         import inspect
#         return inspect.getsource(method)

#     def read_prompt_template(self):
#         return load_prompt_file("correction_prompt.txt")


# def format_input_prompt(improve_prompt, current_method, last_result):
#     separator = '=== SEPARATOR ==='
#     before, after = improve_prompt.split(separator, 1)
#     formatted_before = before.format(current_method, last_result)
#     prompt = formatted_before + separator + after
#     return prompt


# def read_serialize_logic():
#     serialize_logic_path = os.path.join(os.path.dirname(__file__), 'serialize_logic.txt')
#     with open(serialize_logic_path, 'r') as file:
#         code = file.read()
#     return code

# def write_serialize_logic(code):
#     serialize_logic_path = os.path.join(os.path.dirname(__file__), 'serialize_logic.txt')
#     with open(serialize_logic_path, 'w') as file:
#         file.write(code)

# def generate_corrected_serialize_logic(error, current_code):
#     prompt = f"Method code:\n{current_code}\nError:\n{str(error)}\nCorrect the serialize function to handle the error without adding comments or additional text."
#     generator = LlmAnswerGenerator()
#     corrected_code = generator.get_response(prompt)
#     return corrected_code

# def dynamic_serialize(obj):
#     code = read_serialize_logic()
#     local_vars = {}
#     exec(code, globals(), local_vars)
#     serialize = local_vars['serialize']

#     try:
#         return serialize(obj)
#     except Exception as e:
#         print(f"Serialization error: {e}")
#         error_details = traceback.format_exc()
#         corrected_code = generate_corrected_serialize_logic(error_details, code)
#         write_serialize_logic(corrected_code)
#         exec(corrected_code, globals(), local_vars)
#         serialize = local_vars['serialize']
#         return serialize(obj)


# def generate_improved_method(current_method, last_result, iteration):
#     if iteration == 0:
#         prompt_file = "first_prompt.txt"
#     elif iteration == 1:
#         prompt_file = "second_prompt.txt"
#     else:
#         prompt_file = "third_prompt.txt"

#     improve_prompt = load_prompt_file(prompt_file)

#     if 'text' in last_result:
#         last_result.pop('text')

#     last_result_serialized = json.dumps(last_result, default=dynamic_serialize, ensure_ascii=False)

#     prompt = format_input_prompt(improve_prompt, current_method, last_result_serialized)

#     logging.info(f"Prompt being sent to Gemini model:\n{prompt}")

#     generator = LlmAnswerGenerator()
#     improved_method = generator.get_response(prompt)
#     return improved_method


# def generate_context_info(text_content, file_name="", file_extension="", additional_info=""):
#     context_prompt = load_prompt_file("context_prompt.txt")
    
#     if text_content:
#         prompt = context_prompt.format(text_content[:1000])
#     else:
#         prompt = f"File name: {file_name}\nFile extension: {file_extension}\nAdditional info: {additional_info}"
    
#     logging.info(f"Context Prompt being sent to Gemini model:\n{prompt}")

#     generator = LlmAnswerGenerator()
#     context_info = generator.get_response(prompt)
#     return context_info


# def update_method_logic(new_code, file_path):
#     method_logic_path = os.path.join(os.path.dirname(__file__), 'method_logic.py')

#     with open(method_logic_path, 'r') as file:
#         current_code = file.read()

#     with open(method_logic_path, 'w') as file:
#         file.write(new_code)

#     instance = MyClass(file_path=file_path)

#     test_passed = False
#     try:
#         importlib.reload(test_method_logic)
#         test_passed = test_method_logic.test_method_logic(instance)
#     except Exception as e:
#         logging.error(f"Test raised an error: {e}")
#         test_passed = False

#     if test_passed:
#         logging.info("Tests passed. Keeping the new method logic.")
#     else:
#         logging.info("Tests failed. Reverting to the previous method logic.")
#         with open(method_logic_path, 'w') as file:
#             file.write(current_code)