import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import re
import json
import threading
import logging
import google.generativeai as genai
import sys

sys.path.append(os.path.dirname(__file__))
from hs import MyClass, update_method_logic, generate_improved_method
from hs import generate_context_info, clean_info_dict
from file_report import FileReport

# Configure logging for debugging purposes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Retrieve API key and project ID from environment variables
gemini_api_key = os.getenv('GEMINI_API_KEY')
gemini_project_id = os.getenv('GEMINI_PROJECT_ID')

# Validate environment variables
if not gemini_api_key or not gemini_project_id:
    logging.error("Gemini API key and/or Project ID not set in environment variables.")
    raise EnvironmentError("Please set GEMINI_API_KEY and GEMINI_PROJECT_ID environment variables.")

# Configure the Gemini API
genai.configure(api_key=gemini_api_key)
logging.info("Gemini API configured successfully.")

class Application(TkinterDnD.Tk):
    """
    A GUI application to enhance file information extraction with AI-based logic improvement.
    """

    def __init__(self):
        """
        Initializes the application window and its widgets.
        """
        super().__init__()
        self.title("File Info Improvement App")
        self.geometry("640x500")
        self.configure(padx=20, pady=20)

        self.original_method_logic = """
def read_file_info(instance):
    return {'path': instance.file_path}
"""

        self.reset_method_logic()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()

        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'fileinfo_app.ico')
        self.set_app_icon(icon_path)

        self.bind_drop_target()

    def set_app_icon(self, icon_path):
        """
        Sets the window icon.
        
        Args:
            icon_path (str): Path to the icon file.
        """
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Failed to set icon: {e}")

    def bind_drop_target(self):
        """
        Enables drag and drop functionality for file inputs.
        """
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_file_drop)

    def on_file_drop(self, event):
        """
        Handles the event when a file is dropped onto the application.

        Args:
            event (tk.Event): The event object containing file drop data.
        """
        file_path = event.data.strip('{}')
        self.load_input_file(file_path)

    def create_widgets(self):
        """
        Creates and arranges the widgets in the application window.
        """
        self.file_path_label = tk.Label(self, text="Select File:")
        self.file_path_label.pack(pady=5, anchor="w")

        self.file_path_entry = tk.Text(self, width=50, height=3, wrap=tk.WORD)
        self.file_path_entry.pack(pady=5)

        self.file_path_button = tk.Button(self, text="Browse", command=self.browse_file)
        self.file_path_button.pack(pady=5)

        self.improvements_label = tk.Label(self, text="Number of Improvements:")
        self.improvements_label.pack(pady=5, anchor="w")

        self.improvements_entry = tk.Entry(self, width=10)
        self.improvements_entry.pack(pady=5)
        self.improvements_entry.insert(0, "5")

        self.output_path_label = tk.Label(self, text="Output PDF Path:")
        self.output_path_label.pack(pady=5, anchor="w")

        self.output_path_entry = tk.Text(self, width=50, height=3, wrap=tk.WORD)
        self.output_path_entry.pack(pady=5)

        self.output_path_button = tk.Button(self, text="Browse", command=self.browse_output)
        self.output_path_button.pack(pady=5)

        self.generate_button = tk.Button(self, text="Generate Report", command=self.generate_report)
        self.generate_button.pack(pady=20)

        self.progress = ttk.Progressbar(self, orient='horizontal', mode='determinate', length=400)
        self.progress.pack(pady=10)
        self.progress["value"] = 0
        self.progress["maximum"] = 100

        self.generating_label = tk.Label(self, text="", fg="blue")
        self.generating_label.pack(pady=5)

    def reset_method_logic(self):
        """
        Resets the method logic file to its original state.
        """
        method_logic_path = os.path.join(os.path.dirname(__file__), 'method_logic.py')
        with open(method_logic_path, 'w') as file:
            file.write(self.original_method_logic)

    def on_closing(self):
        """
        Handles the window closing event.
        """
        self.reset_method_logic()
        self.destroy()

    def browse_file(self):
        """
        Opens a file dialog to select a file.
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            self.load_input_file(file_path)

    def browse_output(self):
        """
        Opens a file dialog to select the output PDF path.
        """
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if output_path:
            self.output_path_entry.delete(1.0, tk.END)
            self.output_path_entry.insert(tk.END, output_path)

    def load_input_file(self, file_path):
        """
        Loads the input file and updates the UI.

        Args:
            file_path (str): The path to the file selected.
        """
        self.file_path_entry.delete(1.0, tk.END)
        self.file_path_entry.insert(tk.END, file_path)

        output_path = os.path.splitext(file_path)[0] + "_report.pdf"
        self.output_path_entry.delete(1.0, tk.END)
        self.output_path_entry.insert(tk.END, output_path)

        self.reset_method_logic()

    def validate_inputs(self):
        """
        Validates user inputs for file path, output path, and improvements.

        Returns:
            tuple: The validated file path, output path, and improvements.
            bool: False if validation fails.
        """
        try:
            file_path = self.file_path_entry.get("1.0", tk.END).strip()
            output_path = self.output_path_entry.get("1.0", tk.END).strip()
            improvements = int(self.improvements_entry.get())

            if not file_path or not output_path:
                messagebox.showerror("Missing Input", "Please specify both the file path and output path.")
                return False

            if not (1 <= improvements <= 20):
                messagebox.showerror("Invalid Input", "Please enter a number of improvements between 1 and 20.")
                return False

            return file_path, output_path, improvements
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for improvements.")
            return False

    def generate_report(self):
        """
        Generates the report in a separate thread to keep the GUI responsive.
        """
        validated = self.validate_inputs()
        if not validated:
            return

        file_path, output_path, improvements = validated

        threading.Thread(target=self.run_report_generation, args=(file_path, output_path, improvements)).start()

    def update_progress(self, value):
        """
        Updates the progress bar value.

        Args:
            value (int): The progress percentage to set.
        """
        self.progress["value"] = value
        self.update_idletasks()

    def run_report_generation(self, file_path, output_path, improvements):
        """
        Handles the actual report generation process.

        Args:
            file_path (str): The path to the file being processed.
            output_path (str): The path where the PDF report will be saved.
            improvements (int): The number of improvements to apply.
        """
        self.generate_button.config(state=tk.DISABLED)
        self.generating_label.config(text="Generating report...")

        try:
            instance = MyClass(file_path)

            for iteration in range(improvements):
                with open(os.path.join(os.path.dirname(__file__), 'method_logic.py'), 'r') as file:
                    current_method = file.read()

                last_result = instance.dynamic_method()
                text_content = last_result.pop('text', None)
                # logging.info(f'Last result: {last_result}')

                improved_method = generate_improved_method(current_method, last_result, iteration)
                intermediate_logic_path = os.path.join(os.path.dirname(__file__), f'intermediate_logic_iteration_{iteration + 1}.txt')
                with open(intermediate_logic_path, 'w') as file:
                    file.write(improved_method)

                sanitized_method = re.sub(r'^```.*\n', '', improved_method).strip().strip('```').strip()
                sanitized_method = re.sub(r'^python\n', '', sanitized_method).strip()
                
                # logging.info(f"Sanitized Method Logic for Iteration {iteration + 1}:\n{sanitized_method}")

                update_method_logic(sanitized_method, file_path)

                self.update_progress(int((iteration + 1) / improvements * 100))

            final_result = instance.dynamic_method()

            if text_content:
                context_info = generate_context_info(text_content=text_content)
                final_result['text'] = text_content
            else:
                file_extension = os.path.splitext(file_path)[1]
                file_name = os.path.basename(file_path)

                def default_json_serializer(obj):
                    try:
                        if isinstance(obj, bytes):
                            return obj.decode('utf-8', errors='ignore')
                        return str(obj)
                    except Exception as e:
                        logging.warning(f"Skipping non-serializable object: {obj}. Error: {e}")
                        return None

                additional_info = json.dumps(
                    {k: truncate_value(v) for k, v in final_result.items() if 'error' not in str(k).lower() and v is not None and v != ''},
                    indent=2,
                    default=default_json_serializer
                )

                context_info = generate_context_info(None, file_name=file_name, file_extension=file_extension, additional_info=additional_info)

            report = FileReport(clean_info_dict(final_result))
            report.generate_pdf(output_path)

            if context_info:
                report.add_context_info(context_info)

            report.finalize_pdf(output_path)
            logging.info(f"PDF report generated successfully at {output_path}")
            self.reset_method_logic()
            # Automatically open the generated PDF
            self.open_pdf(output_path)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            messagebox.showerror("Error", f"An error occurred during report generation: {e}")
        
        finally:
            # Re-enable the generate button
            self.generate_button.config(state=tk.NORMAL)
            # Reset method logic
            self.reset_method_logic()
            # Reset progress bar
            self.update_progress(0)
            # Hide the generating label
            self.generating_label.config(text="")


    def open_pdf(self, pdf_path):
        """Open the generated PDF with the default system viewer."""
        try:
            if sys.platform == "win32":
                os.startfile(pdf_path)
            elif sys.platform == "darwin":
                os.system(f"open '{pdf_path}'")
            else:
                os.system(f"xdg-open '{pdf_path}'")
        except Exception as e:
            logging.error(f"Failed to open PDF: {e}")
            messagebox.showinfo("Success", f"PDF report generated successfully at {pdf_path}")


def truncate_value(value, max_length=100):
    """Truncate the value if it exceeds max_length."""
    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + '...'
    return value

def main():
    app = Application()
    app.mainloop()

if __name__ == "__main__":
    main()

