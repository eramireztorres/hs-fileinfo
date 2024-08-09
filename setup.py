from setuptools import setup, find_packages

setup(
    name='hs-fileinfo',
    version='1.0.0',
    description='An application that enhances file information extraction with AI-based logic improvement.',
    author='Erick Eduardo Ramirez Torres',
    author_email='erickeduardoramireztorres@gmail.com',
    url='https://github.com/eramireztorres/hs_fileinfo',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['**/*.txt', 'icons/*.ico'],  # Include all .txt files and .ico files in the specified directories
    },
    install_requires=[
        'google-generativeai',        
        'fpdf2',
        'pandas',
        'matplotlib==3.8.2',
        'seaborn',
        'plotly',
        'Pillow',
        'pydub',
        'nltk',
        'wordcloud',
        'pytesseract',
        'numpy',
        'scipy',
        'librosa',
        'PyPDF2',
        'pdf2image',
        'openpyxl',
        'python-docx',
        'python-pptx',
        'sqlalchemy',
        'h5py',
        'tqdm',
        'opencv-python',
        'ffmpeg-python',
        'moviepy',
        'joblib',
        'patool',
        'py7zr',
        'python-magic',
        'python-magic-bin',
        'rarfile',
        'xlrd',
        'mutagen',
        'cairosvg',
        'lxml',
        'odfpy',
        'epub',
        'regipy',
        'mido',
        'markdown',
        'configparser',
        'python-chess',
        'ebooklib',
        'svgpathtools',
        'selenium',
        'html2text',
        'bs4'
    ],
    
    entry_points={
        'console_scripts': [
            'hs_fileinfo=src.fileinfo_gui:main',  # Assuming main is the function you want to execute
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
