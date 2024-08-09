from fpdf import FPDF
import os
import logging

class PDFElement:
    def __init__(self, pdf):
        self.pdf = pdf

    def set_font(self, font="Times", style="", size=12):
        self.pdf.set_font(font, style, size)

    def add_multicell(self, text, border=0, align='L', width=0):
        # Adds a multi-cell with text and dynamic width
        self.pdf.multi_cell(width, 10, text, border=border, align=align)

    def add_cell(self, text, width=40, border=0, align='L'):
        # Adds a single cell with text
        self.pdf.cell(width, 10, text, border=border, align=align)

    def add_line_break(self, height=5):
        self.pdf.ln(height)

    def add_image(self, image_path, width=100):
        try:
            self.pdf.image(image_path, w=width)
            self.add_line_break(10)
        except Exception as e:
            logging.error(f"Failed to add image: {e}")
            self.add_multicell(f"Failed to add image: {e}")

class FileReport:
    def __init__(self, data):
        self.data = self.sanitize_data(data)
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_left_margin(10)
        self.pdf.set_right_margin(10)
        self.max_text_length = 500  # Example threshold for text data

    def sanitize_data(self, data):
        # Sanitize the input data to remove None or empty-string values
        return {k: v for k, v in data.items() if v not in (None, '', 'error')}

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
        element = PDFElement(self.pdf)
        element.set_font("Times", 'B', size=16)
        sanitized_title = self.sanitize_text(title)
        
        # Handle long titles
        max_title_length = 60  # Example threshold for title length
        if len(sanitized_title) > max_title_length:
            sanitized_title = sanitized_title[:max_title_length - 3] + "..."  # Truncate with ellipsis
        
        # Use multi_cell for better text handling
        element.add_multicell(sanitized_title, align='C', width=0)
        element.set_font(size=12)
        element.add_line_break(10)

    def add_subtitle(self, subtitle):
        element = PDFElement(self.pdf)
        element.set_font("Times", 'B', size=14)
        sanitized_subtitle = self.sanitize_text(subtitle)
        element.add_multicell(sanitized_subtitle, align='L', width=0)
        element.set_font(size=12)
        element.add_line_break(5)

    def add_text(self, text):
        element = PDFElement(self.pdf)
        sanitized_text = self.sanitize_text(text)
        element.add_multicell(sanitized_text, width=0)
        element.add_line_break(5)

    def add_key_value(self, key, value):
        element = PDFElement(self.pdf)
        element.set_font("Times", 'B', size=12)
        sanitized_key = self.sanitize_text(key + ":")
        
        # Calculate the width of the key text to dynamically adjust placement of value
        key_width = self.pdf.get_string_width(sanitized_key) + 5  # Add some padding
        element.add_cell(sanitized_key, width=key_width)
        
        element.set_font(size=12)
        sanitized_value = self.sanitize_text(str(value))
        
        # Use multi-cell for the value to wrap it within page margins
        available_width = self.pdf.w - self.pdf.r_margin - self.pdf.get_x()  # Calculate remaining width
        element.add_multicell(' ' + sanitized_value, width=available_width)
        
        element.add_line_break(5)

    def add_image_with_caption(self, image_path, caption):
        element = PDFElement(self.pdf)
        self.add_subtitle(caption)
        if os.path.exists(image_path):
            element.add_image(image_path, width=100)
        else:
            element.add_multicell(f"Image not found or unsupported format: {image_path}")

    def is_valid_text(self, text):
        return isinstance(text, str) and len(text) <= self.max_text_length

    def add_context_info(self, context_info):
        self.add_subtitle("Contextual Information")
        self.add_text(context_info)

    def generate_pdf(self, output_path, include_errors=False):
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
            
            if 'path' in str(key).lower():
                continue
            
            logging.info(f'Key: {key} Value {value}')
    
            if 'error' in key and not include_errors:
                # Skip the error key if include_errors is False
                continue
            
            try:
                if value == '':
                    continue
            except:
                pass
    
            if isinstance(value, str) and self.is_valid_text(value) and not os.path.isfile(value):
                self.add_key_value(key.replace('_', ' ').title(), value)
            elif isinstance(value, (int, float)):
                self.add_key_value(key.replace('_', ' ').title(), value)
            elif isinstance(value, list) and len(value) <= self.max_text_length:
                self.add_key_value(key.replace('_', ' ').title(), ', '.join(map(str, value)))
            elif isinstance(value, str) and os.path.exists(value) and self.is_supported_image(value):
                self.add_image_with_caption(value, key)
                if value == self.data['path']:
                    image_path_included = True
    
        # Check if path is an image and not included elsewhere
        path_is_image = self.is_supported_image(self.data['path'])
        if path_is_image and not image_path_included:
            self.add_image_with_caption(self.data['path'], "Image:")
    
    def is_supported_image(self, file_path):
        """Check if the file is a supported image format."""
        supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff')
        return file_path.lower().endswith(supported_extensions)

    def finalize_pdf(self, output_path):
        # Output the PDF
        self.pdf.output(output_path)




# from fpdf import FPDF
# import os
# import logging

# class PDFElement:
#     def __init__(self, pdf):
#         self.pdf = pdf

#     def set_font(self, font="Times", style="", size=12):
#         self.pdf.set_font(font, style, size)

#     def add_multicell(self, text, border=0, align='L'):
#         # Adds a multi-cell with text
#         self.pdf.multi_cell(0, 10, text, border=border, align=align)

#     def add_cell(self, text, width=40, border=0, align='L'):
#         # Adds a single cell with text
#         self.pdf.cell(width, 10, text, border=border, align=align)

#     def add_line_break(self, height=5):
#         self.pdf.ln(height)

#     def add_image(self, image_path, width=100):
#         try:
#             self.pdf.image(image_path, w=width)
#             self.add_line_break(10)
#         except Exception as e:
#             logging.error(f"Failed to add image: {e}")
#             self.add_multicell(f"Failed to add image: {e}")

# class FileReport:
#     def __init__(self, data):
#         self.data = self.sanitize_data(data)
#         self.pdf = FPDF()
#         self.pdf.add_page()
#         self.pdf.set_left_margin(10)
#         self.pdf.set_right_margin(10)
#         self.max_text_length = 500  # Example threshold for text data

#     def sanitize_data(self, data):
#         # Sanitize the input data to remove None or empty-string values
#         return {k: v for k, v in data.items() if v not in (None, '', 'error')}

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
#         element = PDFElement(self.pdf)
#         element.set_font("Times", 'B', size=16)
#         sanitized_title = self.sanitize_text(title)
        
#         # Handle long titles
#         max_title_length = 60  # Example threshold for title length
#         if len(sanitized_title) > max_title_length:
#             sanitized_title = sanitized_title[:max_title_length - 3] + "..."  # Truncate with ellipsis
        
#         # Use multi_cell for better text handling
#         element.add_multicell(sanitized_title, align='C')
#         element.set_font(size=12)
#         element.add_line_break(10)

#     def add_subtitle(self, subtitle):
#         element = PDFElement(self.pdf)
#         element.set_font("Times", 'B', size=14)
#         sanitized_subtitle = self.sanitize_text(subtitle)
#         element.add_multicell(sanitized_subtitle, align='L')
#         element.set_font(size=12)
#         element.add_line_break(5)

#     def add_text(self, text):
#         element = PDFElement(self.pdf)
#         sanitized_text = self.sanitize_text(text)
#         element.add_multicell(sanitized_text)
#         element.add_line_break(5)

#     def add_key_value(self, key, value):
#         element = PDFElement(self.pdf)
#         element.set_font("Times", 'B', size=12)
#         sanitized_key = self.sanitize_text(key + ":")
#         element.add_cell(sanitized_key)
#         element.set_font(size=12)
#         sanitized_value = self.sanitize_text(str(value))
#         element.add_multicell(' ' + sanitized_value)
#         element.add_line_break(5)

#     def add_image_with_caption(self, image_path, caption):
#         element = PDFElement(self.pdf)
#         self.add_subtitle(caption)
#         if os.path.exists(image_path):
#             element.add_image(image_path, width=100)
#         else:
#             element.add_multicell(f"Image not found or unsupported format: {image_path}")

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
#                 self.add_image_with_caption(value, key)
#                 if value == self.data['path']:
#                     image_path_included = True
    
#         # Check if path is an image and not included elsewhere
#         path_is_image = self.is_supported_image(self.data['path'])
#         if path_is_image and not image_path_included:
#             self.add_image_with_caption(self.data['path'], "Image:")
    
#     def is_supported_image(self, file_path):
#         """Check if the file is a supported image format."""
#         supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff')
#         return file_path.lower().endswith(supported_extensions)

#     def finalize_pdf(self, output_path):
#         # Output the PDF
#         self.pdf.output(output_path)




# import os
# from fpdf import FPDF

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
        
#         # Handle long titles
#         max_title_length = 60  # Example threshold for title length
#         if len(sanitized_title) > max_title_length:
#             sanitized_title = sanitized_title[:max_title_length - 3] + "..."  # Truncate with ellipsis
        
#         # Use multi_cell for better text handling
#         self.pdf.multi_cell(0, 10, sanitized_title, align='C')
#         self.pdf.set_font("Times", size=12)
#         self.pdf.ln(10)

#     def add_subtitle(self, subtitle):
#         self.pdf.set_font("Times", 'B', size=14)
#         sanitized_subtitle = self.sanitize_text(subtitle)
#         self.pdf.multi_cell(0, 10, sanitized_subtitle, align='L')
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
#                 # Adjust image width and maintain aspect ratio
#                 image_width = 100
#                 self.pdf.image(image_path, w=image_width)
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
