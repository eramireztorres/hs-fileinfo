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
    """
    A class to generate PDF reports for file information extracted by the dynamic method.

    Attributes:
        data (dict): The dictionary containing file information.
        pdf (FPDF): The FPDF object for PDF generation.
        max_text_length (int): The maximum allowed length for text data.
    """

    def __init__(self, data):
        """
        Initializes the FileReport with extracted file information.

        Args:
            data (dict): The dictionary containing file information.
        """
        self.data = self.sanitize_data(data)
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_left_margin(10)
        self.pdf.set_right_margin(10)
        self.max_text_length = 500  # Example threshold for text data

    def sanitize_data(self, data):
        """
        Sanitizes the input data by removing entries with None or empty string values.

        Args:
            data (dict): The dictionary to be sanitized.

        Returns:
            dict: The sanitized dictionary.
        """
        return {k: v for k, v in data.items() if v not in (None, '', 'error')}

    def sanitize_text(self, text):
        """
        Removes any character that raises a UnicodeEncodeError when using Times font.

        Args:
            text (str): The text to be sanitized.

        Returns:
            str: The sanitized text.
        """
        sanitized_text = ""
        for char in text:
            try:
                char.encode("latin-1")
                sanitized_text += char
            except UnicodeEncodeError:
                continue
        return sanitized_text

    def add_title(self, title):
        """
        Adds a title to the PDF report.

        Args:
            title (str): The title text.
        """
        element = PDFElement(self.pdf)
        element.set_font("Times", 'B', size=16)
        sanitized_title = self.sanitize_text(title)

        max_title_length = 60  # Example threshold for title length
        if len(sanitized_title) > max_title_length:
            sanitized_title = sanitized_title[:max_title_length - 3] + "..."  # Truncate with ellipsis

        element.add_multicell(sanitized_title, align='C', width=0)
        element.set_font(size=12)
        element.add_line_break(10)

    def add_subtitle(self, subtitle):
        """
        Adds a subtitle to the PDF report.

        Args:
            subtitle (str): The subtitle text.
        """
        element = PDFElement(self.pdf)
        element.set_font("Times", 'B', size=14)
        sanitized_subtitle = self.sanitize_text(subtitle)
        element.add_multicell(sanitized_subtitle, align='L', width=0)
        element.set_font(size=12)
        element.add_line_break(5)

    def add_text(self, text):
        """
        Adds general text to the PDF report.

        Args:
            text (str): The text to be added.
        """
        element = PDFElement(self.pdf)
        sanitized_text = self.sanitize_text(text)
        element.add_multicell(sanitized_text, width=0)
        element.add_line_break(5)

    def add_key_value(self, key, value):
        """
        Adds a key-value pair to the PDF report.

        Args:
            key (str): The key text.
            value (str): The value associated with the key.
        """
        element = PDFElement(self.pdf)
        element.set_font("Times", 'B', size=12)
        sanitized_key = self.sanitize_text(key + ":")

        key_width = self.pdf.get_string_width(sanitized_key) + 5  # Add some padding
        element.add_cell(sanitized_key, width=key_width)

        element.set_font(size=12)
        sanitized_value = self.sanitize_text(str(value))

        available_width = self.pdf.w - self.pdf.r_margin - self.pdf.get_x()  # Calculate remaining width
        element.add_multicell(' ' + sanitized_value, width=available_width)

        element.add_line_break(5)

    def add_image_with_caption(self, image_path, caption):
        """
        Adds an image with a caption to the PDF report.

        Args:
            image_path (str): The path to the image file.
            caption (str): The caption text for the image.
        """
        element = PDFElement(self.pdf)
        self.add_subtitle(caption)
        if os.path.exists(image_path):
            element.add_image(image_path, width=100)
        else:
            element.add_multicell(f"Image not found or unsupported format: {image_path}")

    def is_valid_text(self, text):
        """
        Checks if the text is valid based on type and length.

        Args:
            text (str): The text to be checked.

        Returns:
            bool: True if valid, False otherwise.
        """
        return isinstance(text, str) and len(text) <= self.max_text_length

    def add_context_info(self, context_info):
        """
        Adds contextual information to the PDF report.

        Args:
            context_info (str): The contextual information text.
        """
        self.add_subtitle("Contextual Information")
        self.add_text(context_info)

    def generate_pdf(self, output_path, include_errors=False):
        """
        Generates a PDF report of the extracted information.

        Parameters:
            output_path (str): The path where the PDF report will be saved.
            include_errors (bool): Whether to include errors in the report. Defaults to True.
        """
        file_name = os.path.basename(self.data['path'])
        self.add_title(f"{file_name} Report")

        self.add_subtitle("File Path")
        self.add_text(self.data['path'])

        image_path_included = False

        for key, value in self.data.items():
            if 'path' in str(key).lower():
                continue
    
            if 'error' in str(key).lower() and not include_errors:
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

        path_is_image = self.is_supported_image(self.data['path'])
        if path_is_image and not image_path_included:
            self.add_image_with_caption(self.data['path'], "Image:")

    def is_supported_image(self, file_path):
        """
        Checks if the file is a supported image format.

        Args:
            file_path (str): The path to the file.

        Returns:
            bool: True if the file is a supported image format, False otherwise.
        """
        supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff')
        return file_path.lower().endswith(supported_extensions)

    def finalize_pdf(self, output_path):
        """
        Outputs the PDF to the specified file path.

        Args:
            output_path (str): The path where the PDF will be saved.
        """
        self.pdf.output(output_path)


