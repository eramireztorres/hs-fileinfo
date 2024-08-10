# hs-fileinfo
The Hot-Swapping Fileinfo App is a Python-based tool that extracts detailed information from various file types. Utilizing the Gemini model, the app dynamically improves its extraction methods to provide comprehensive data analysis and visualization for supported file formats, including images, documents, audio, and programming files.

## What You Can Do

With the Hot-Swapping Fileinfo App, you can:

- **Analyze Various File Types:** Extract metadata and content from a wide range of file formats such as images (JPG, PNG, SVG), documents (PDF, DOCX, XLSX), audio files (MP3, WAV), and more.
- **Dynamic Method Improvement:** The app iteratively improves its methods for extracting file information, adapting based on the file content.
- **Report Generation:** Generate detailed PDF reports summarizing the extracted information, complete with contextual insights.

## Tips for Use

- If the initial extraction doesn't yield the desired result, try running the report generation process multiple times, increasing the number of improvements. The app will continue refining its methods with each improvement, potentially leading to better results.

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
    pip install .
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

5. **Run the app:**
    ```bash
    hs_fileinfo
    ```
    
## License
Hot-Swapping Fileinfo is licensed under the MIT License.