import json
import logging
import os
import importlib
import traceback
import time
from datetime import datetime
import sys
import inspect

import pkg_resources

def load_prompt_file(filename):
    """Loads a text file from the installed package data."""
    resource_package = __name__  # name of the package where this module is located
    resource_path = f'prompts/{filename}'  # Do not use os.path.join() here
    return pkg_resources.resource_string(resource_package, resource_path).decode('utf-8')

# from tests import test_method_logic
# from src.gemini_api import GeminiAPI

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests'))
import test_method_logic
from gemini_api import GeminiAPI

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
    """
    A class to dynamically modify and execute a method from an external Python module.

    Attributes:
        file_path (str): The path to the file that is being processed.
    """

    def __init__(self, file_path):
        """
        Initializes MyClass with the provided file path.

        Args:
            file_path (str): The path to the file.
        """
        self.file_path = file_path

    def dynamic_method(self, retries=3, delay_duration=5):
        """
        Attempts to execute a dynamically loaded method, correcting it if an error occurs.

        Args:
            retries (int): The number of retry attempts if an error occurs.
            delay_duration (int): The time to wait (in seconds) before retrying after an error.

        Returns:
            dict: The result of the method execution.

        Raises:
            RuntimeError: If all correction attempts fail.
        """
        sys.path.append(os.path.dirname(__file__))
        module_name = 'method_logic'
        method_name = 'read_file_info'

        for attempt in range(retries):
            try:
                # Invalidate caches and force reload the module
                importlib.invalidate_caches()
                if module_name in sys.modules:
                    del sys.modules[module_name]

                module = importlib.import_module(module_name)
                importlib.reload(module)
                method = getattr(module, method_name)

                # Execute the method
                result = method(self)

                # Validate output
                self.validate_output(result)

                return result

            except Exception as e:
                logging.error(f"Error in method execution: {e}")
                logging.info(f"Delaying request by {delay_duration} seconds due to fix attempt {attempt + 1}")
                time.sleep(delay_duration)

                corrected_code = self.correct_method_code(method_name, method, e)
                self.apply_corrected_method(module_name, corrected_code)

        raise RuntimeError("All correction attempts failed.")

    def validate_output(self, result):
        """
        Validates the result of the dynamically loaded method.

        Args:
            result (dict): The output from the dynamically executed method.

        Raises:
            ValueError: If the 'path' key is not present in the result.
        """
        if 'path' not in result:
            raise ValueError("The 'path' key is not present in the output. Validation failed.")

    def correct_method_code(self, method_name, method, error):
        """
        Corrects the method code based on the error encountered.

        Args:
            method_name (str): The name of the method to correct.
            method (function): The method object.
            error (Exception): The error encountered during method execution.

        Returns:
            str: The corrected method code.
        """
        current_code = self.get_method_code(method_name, method)
        prompt_template = self.read_prompt_template()

        # Format the prompt with the current code and error details
        prompt = prompt_template.format(current_code=current_code, error_details=str(error))

        # Generate the corrected method code using an external generator
        generator = LlmAnswerGenerator()
        corrected_code = generator.get_response(prompt)
        return corrected_code

    def apply_corrected_method(self, module_name, corrected_code):
        """
        Applies the corrected method code by writing it to the module and reloading it.

        Args:
            module_name (str): The name of the module containing the method.
            corrected_code (str): The corrected method code.
        """
        method_logic_path = os.path.join(os.path.dirname(__file__), f'{module_name}.py')
        with open(method_logic_path, 'w') as file:
            file.write(corrected_code)
        importlib.reload(importlib.import_module(module_name))

    def get_method_code(self, method_name, method):
        """
        Retrieves the source code of the method.

        Args:
            method_name (str): The name of the method.
            method (function): The method object.

        Returns:
            str: The source code of the method.
        """
        return inspect.getsource(method)

    def read_prompt_template(self):
        """
        Reads the prompt template from a file.

        Returns:
            str: The content of the prompt template.
        """
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



def generate_improved_method(current_method, last_result, iteration, delay_between_calls=True, 
                             delay_duration=2):
    """
    Generates an improved method using the Gemini model.

    Parameters:
    - current_method (str): The current method code to be improved.
    - last_result (dict): The result from the last execution to be used for context.
    - iteration (int): The current iteration number.
    - delay_between_calls (bool): Whether to introduce a delay before making the request. Defaults to False.
    - delay_duration (int): The duration of the delay in seconds if delay_between_calls is True. Defaults to 2 seconds.

    Returns:
    - str: The improved method code generated by the Gemini model.
    """
    # Determine which prompt file to use based on iteration
    prompt_file = {
        0: "first_prompt.txt",
        1: "second_prompt.txt",
    }.get(iteration, "third_prompt.txt")

    # Load the appropriate prompt
    improve_prompt = load_prompt_file(prompt_file)

    # Remove 'text' from the last_result if present
    last_result.pop('text', None)

    # Serialize last_result, ensuring non-ASCII characters are handled properly
    last_result_serialized = json.dumps(last_result, default=safe_serialize, ensure_ascii=False)

    # Format the input prompt with the current method and serialized last_result
    prompt = format_input_prompt(improve_prompt, current_method, last_result_serialized)

    # Introduce a delay if specified and iteration is greater than zero
    if delay_between_calls and iteration > 0:
        logging.info(f"Delaying request by {delay_duration} seconds due to iteration {iteration}")
        time.sleep(delay_duration)

    # Generate the improved method using the Gemini model
    generator = LlmAnswerGenerator()
    improved_method = generator.get_response(prompt)

    return improved_method


def generate_context_info(text_content, file_name="", file_extension="", additional_info=""):
        
    if text_content:
        context_prompt = load_prompt_file("context_prompt.txt")
        prompt = context_prompt.format(text_content[:1000])
    else:
        extension_context_prompt = load_prompt_file("extension_context_prompt.txt")
        prompt = extension_context_prompt.format(file_name, file_extension, additional_info)

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

def clean_info_dict(info_dict):
    """
    Cleans the given dictionary by removing entries with keys 'error',
    and entries with None or empty string values.

    Args:
        info_dict (dict): The dictionary to be cleaned.

    Returns:
        dict: A new dictionary with unwanted entries removed.
    """
    cleaned_dict = {
        key: value
        for key, value in info_dict.items()
        if key != 'error' and value not in (None, '', [])
    }
    return cleaned_dict

class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

def safe_serialize(obj):
    try:
        return json.dumps(obj, cls=SafeEncoder)
    except Exception as e:
        logging.error(f"Serialization error: {e}")
        return ""

