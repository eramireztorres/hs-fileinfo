import os
from fpdf import FPDF

class FileReport:
    def __init__(self, data):
        self.data = data
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_font("Times", size=12)
        self.pdf.set_left_margin(10)
        self.pdf.set_right_margin(10)
        self.max_text_length = 500  # Example threshold for text data

    def sanitize_text(self, text):
        """
        Remove any character that raises a UnicodeEncodeError when using Times font.
        """
        sanitized_text = ""
        for char in text:
            try:
                char.encode("latin-1")
                sanitized_text += char
            except UnicodeEncodeError:
                # Remove unsupported character
                continue
        return sanitized_text

    def add_title(self, title):
        self.pdf.set_font("Times", 'B', size=16)
        sanitized_title = self.sanitize_text(title)
        
        # Handle long titles
        max_title_length = 60  # Example threshold for title length
        if len(sanitized_title) > max_title_length:
            sanitized_title = sanitized_title[:max_title_length - 3] + "..."  # Truncate with ellipsis
        
        # Use multi_cell for better text handling
        self.pdf.multi_cell(0, 10, sanitized_title, align='C')
        self.pdf.set_font("Times", size=12)
        self.pdf.ln(10)

    def add_subtitle(self, subtitle):
        self.pdf.set_font("Times", 'B', size=14)
        sanitized_subtitle = self.sanitize_text(subtitle)
        self.pdf.multi_cell(0, 10, sanitized_subtitle, align='L')
        self.pdf.set_font("Times", size=12)
        self.pdf.ln(5)

    def add_text(self, text):
        sanitized_text = self.sanitize_text(text)
        self.pdf.multi_cell(0, 10, sanitized_text)
        self.pdf.ln(5)

    def add_key_value(self, key, value):
        self.pdf.set_font("Times", 'B', size=12)
        sanitized_key = self.sanitize_text(key + ":")
        self.pdf.cell(40, 10, sanitized_key)
        self.pdf.set_font("Times", size=12)
        sanitized_value = self.sanitize_text(str(value))
        self.pdf.multi_cell(0, 10, ' ' + sanitized_value)
        self.pdf.ln(5)

    def add_image(self, image_path, title):
        if os.path.exists(image_path):
            self.add_subtitle(title.replace('_', ' ').title())
            try:
                # Adjust image width and maintain aspect ratio
                image_width = 100
                self.pdf.image(image_path, w=image_width)
                self.pdf.ln(10)
            except Exception as e:
                self.add_text(f"Failed to add image: {e}")
        else:
            self.add_text(f"Image not found or unsupported format: {image_path}")

    def is_valid_text(self, text):
        return isinstance(text, str) and len(text) <= self.max_text_length

    def add_context_info(self, context_info):
        self.add_subtitle("Contextual Information")
        self.add_text(context_info)

    def generate_pdf(self, output_path, include_errors=True):
        """
        Generates a PDF report of the extracted information.
    
        Parameters:
        - output_path (str): The path where the PDF report will be saved.
        - include_errors (bool): Whether to include errors in the report. Defaults to True.
        """
        # Extract file name without path
        file_name = os.path.basename(self.data['path'])
        # Add the file name as title
        self.add_title(f"{file_name} Report")
    
        # Add file path subtitle and content
        self.add_subtitle("File Path")
        self.add_text(self.data['path'])
    
        # Track if the image path is used elsewhere
        image_path_included = False
    
        # Add other keys information
        for key, value in self.data.items():
            if key == 'path':
                continue
    
            if key == 'error' and not include_errors:
                # Skip the error key if include_errors is False
                continue
    
            if isinstance(value, str) and self.is_valid_text(value) and not os.path.isfile(value):
                self.add_key_value(key.replace('_', ' ').title(), value)
            elif isinstance(value, (int, float)):
                self.add_key_value(key.replace('_', ' ').title(), value)
            elif isinstance(value, list) and len(value) <= self.max_text_length:
                self.add_key_value(key.replace('_', ' ').title(), ', '.join(map(str, value)))
            elif isinstance(value, str) and os.path.exists(value) and self.is_supported_image(value):
                self.add_image(value, key)
                if value == self.data['path']:
                    image_path_included = True
    
        # Check if path is an image and not included elsewhere
        path_is_image = self.is_supported_image(self.data['path'])
        if path_is_image and not image_path_included:
            self.add_image(self.data['path'], "Image:")
    
    def is_supported_image(self, file_path):
        """Check if the file is a supported image format."""
        supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff')
        return file_path.lower().endswith(supported_extensions)

    def finalize_pdf(self, output_path):
        # Output the PDF
        self.pdf.output(output_path)


# class FileReport:
#     def __init__(self, data):
#         self.data = data
#         self.pdf = FPDF()
#         self.pdf.add_page()
#         self.pdf.set_font("Times", size=12)
#         self.pdf.set_left_margin(10)
#         self.pdf.set_right_margin(10)
#         self.max_text_length = 500  # Example threshold for text data

#     def sanitize_text(self, text):
#         """
#         Remove any character that raises a UnicodeEncodeError when using Times font.
#         """
#         sanitized_text = ""
#         for char in text:
#             try:
#                 char.encode("latin-1")
#                 sanitized_text += char
#             except UnicodeEncodeError:
#                 # Remove unsupported character
#                 continue
#         return sanitized_text

#     def add_title(self, title):
#         self.pdf.set_font("Times", 'B', size=16)
#         sanitized_title = self.sanitize_text(title)
#         self.pdf.cell(0, 10, sanitized_title, ln=True, align='C')
#         self.pdf.set_font("Times", size=12)
#         self.pdf.ln(10)

#     def add_subtitle(self, subtitle):
#         self.pdf.set_font("Times", 'B', size=14)
#         sanitized_subtitle = self.sanitize_text(subtitle)
#         self.pdf.cell(0, 10, sanitized_subtitle, ln=True, align='L')
#         self.pdf.set_font("Times", size=12)
#         self.pdf.ln(5)

#     def add_text(self, text):
#         sanitized_text = self.sanitize_text(text)
#         self.pdf.multi_cell(0, 10, sanitized_text)
#         self.pdf.ln(5)

#     def add_key_value(self, key, value):
#         self.pdf.set_font("Times", 'B', size=12)
#         sanitized_key = self.sanitize_text(key + ":")
#         self.pdf.cell(40, 10, sanitized_key)
#         self.pdf.set_font("Times", size=12)
#         sanitized_value = self.sanitize_text(str(value))
#         self.pdf.multi_cell(0, 10, ' ' + sanitized_value)
#         self.pdf.ln(5)

#     def add_image(self, image_path, title):
#         if os.path.exists(image_path):
#             self.add_subtitle(title.replace('_', ' ').title())
#             try:
#                 self.pdf.image(image_path, w=100)  # Adjust the width as needed
#                 self.pdf.ln(10)
#             except Exception as e:
#                 self.add_text(f"Failed to add image: {e}")
#         else:
#             self.add_text(f"Image not found or unsupported format: {image_path}")

#     def is_valid_text(self, text):
#         return isinstance(text, str) and len(text) <= self.max_text_length

#     def add_context_info(self, context_info):
#         self.add_subtitle("Contextual Information")
#         self.add_text(context_info)

#     def generate_pdf(self, output_path, include_errors=True):
#         """
#         Generates a PDF report of the extracted information.
    
#         Parameters:
#         - output_path (str): The path where the PDF report will be saved.
#         - include_errors (bool): Whether to include errors in the report. Defaults to True.
#         """
#         # Extract file name without path
#         file_name = os.path.basename(self.data['path'])
#         # Add the file name as title
#         self.add_title(f"{file_name} Report")
    
#         # Add file path subtitle and content
#         self.add_subtitle("File Path")
#         self.add_text(self.data['path'])
    
#         # Track if the image path is used elsewhere
#         image_path_included = False
    
#         # Add other keys information
#         for key, value in self.data.items():
#             if key == 'path':
#                 continue
    
#             if key == 'error' and not include_errors:
#                 # Skip the error key if include_errors is False
#                 continue
    
#             if isinstance(value, str) and self.is_valid_text(value) and not os.path.isfile(value):
#                 self.add_key_value(key.replace('_', ' ').title(), value)
#             elif isinstance(value, (int, float)):
#                 self.add_key_value(key.replace('_', ' ').title(), value)
#             elif isinstance(value, list) and len(value) <= self.max_text_length:
#                 self.add_key_value(key.replace('_', ' ').title(), ', '.join(map(str, value)))
#             elif isinstance(value, str) and os.path.exists(value) and self.is_supported_image(value):
#                 self.add_image(value, key)
#                 if value == self.data['path']:
#                     image_path_included = True
    
#         # Check if path is an image and not included elsewhere
#         path_is_image = self.is_supported_image(self.data['path'])
#         if path_is_image and not image_path_included:
#             self.add_image(self.data['path'], "Image:")
    
#     def is_supported_image(self, file_path):
#         """Check if the file is a supported image format."""
#         supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff')
#         return file_path.lower().endswith(supported_extensions)



#     def finalize_pdf(self, output_path):
#         # Output the PDF
#         self.pdf.output(output_path)
