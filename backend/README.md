# Book Translation API

An advanced FastAPI-based backend service for translating books and PDF documents using OpenAI's language models.

## Features

- **PDF Processing**: Upload and process PDF files for translation
- **Chapter-based Translation**: Submit book chapters for translation individually or in bulk
- **Asynchronous Processing**: All translations are processed asynchronously with progress tracking
- **Format Conversion**: Convert translated content to PDF or DOCX formats
- **Multiple Languages**: Support for translating to various target languages
- **Robust Error Handling**: Comprehensive error handling and retry mechanisms
- **OpenAI Compatibility**: Works with both legacy (0.x) and modern (1.x+) OpenAI API clients

## Installation

### Using pip

```bash
# Clone repository
git clone https://github.com/your-username/tradutor_livro.git
cd tradutor_livro/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Using setup.sh

```bash
# Clone repository
git clone https://github.com/your-username/tradutor_livro.git
cd tradutor_livro/backend

# Run setup script
chmod +x setup.sh
./setup.sh
```

## Configuration

Create a `.env` file in the `backend` directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
PORT=8000
LOG_LEVEL=INFO
USE_BACKGROUND_TASKS=1
MAX_FILE_SIZE=10485760  # 10MB in bytes
MAX_CHAPTERS=100
```

## Usage

### Running the server

```bash
# Start the server
python -m app.main

# Or use the console script
book-translator

# With custom port and reload
PORT=8080 RELOAD=true book-translator
```

### API Endpoints

- **GET /** - API information
- **POST /api/translation/translate** - Submit book chapters for translation
- **GET /api/translation/status/{job_id}** - Check translation status
- **GET /api/translation/download/{job_id}** - Download translated document
- **POST /api/upload/pdf** - Upload a PDF file for translation

Detailed API documentation is available at `/docs` when the server is running.

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/                 # API routes
│   ├── core/                # Core functionality
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   └── main.py              # Application entry point
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── setup.py                # Package configuration
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --unit
python run_tests.py --api
python run_tests.py --e2e

# Generate coverage report
python run_tests.py --coverage

# Generate HTML report
python run_tests.py --html
```

## Troubleshooting

### OpenAI Version Issues

If you encounter OpenAI version compatibility issues, try:

```bash
# For older projects using legacy syntax
pip uninstall -y openai
pip install openai==0.28.1

# For modern code
pip uninstall -y openai
pip install openai>=1.0.0
```

The application includes a version-agnostic OpenAI client that should work with either version.

### Port Already in Use

The server will automatically try the next available port if the default one is in use. You can also specify a different port:

```bash
PORT=8080 python -m app.main
```

## License

MIT 