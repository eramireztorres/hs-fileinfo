# hs-fileinfo
The Hot-Swapping Fileinfo App is a Python-based tool that extracts detailed information from various file types. Utilizing the Gemini model, the app dynamically improves its extraction methods to provide comprehensive data analysis and visualization for supported file formats, including images, documents, audio, and programming files.

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account for the Gemini API

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/eramireztorres/hs-fileinfo.git
   cd hs-fileinfo   
   ```
2. **Set up a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    ```
  
3. **Install the required packages:**
    Run the following command to install dependencies:
    ```bash
    python setup.py install
    ```
    
4. **Set up your Google Cloud API key and Project ID as environment variables:**
    ```bash
    export GEMINI_API_KEY='your-api-key'
    export GEMINI_PROJECT_ID='your-project-id'
    ```
    
    On Windows, you can set environment variables using:
    
    ```bash
    setx GEMINI_API_KEY your-api-key
    setx GEMINI_PROJECT_ID your-project-id
    ```

