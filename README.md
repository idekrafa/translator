# 📚 Book Translator

A modern, full-stack application for translating books and PDF documents using OpenAI's language models, with professional formatting for print publication.

## ✨ Features

- **📄 PDF Processing**: Upload and process PDF files for automatic translation
- **📖 Chapter-based Translation**: Manual chapter input with professional formatting
- **🔄 Asynchronous Processing**: Real-time progress tracking for translations
- **📑 Multiple Formats**: Generate DOCX and PDF outputs with book-style formatting
- **🌍 Multi-language Support**: Translate to Portuguese, Spanish, French, German, Italian, Japanese, Chinese, Korean
- **🎨 Professional Layout**: 6x9 inch book format with proper typography and pagination
- **⚡ Modern Tech Stack**: FastAPI backend, React frontend, Docker deployment
- **🧪 Comprehensive Testing**: Unit, integration, and end-to-end tests

## 🏗️ Architecture

- **Backend**: FastAPI + Python with OpenAI GPT-4 integration
- **Frontend**: React + TypeScript with Tailwind CSS
- **Processing**: Async job queue with real-time progress updates
- **Storage**: Local file system with configurable output directory
- **Deployment**: Docker Compose for easy containerization

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ 
- Node.js 18+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Docker & Docker Compose (optional, for containerized deployment)

### Automated Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd translator

# Run the setup script (handles everything automatically)
chmod +x setup-project.sh
./setup-project.sh

# Add your OpenAI API key to backend/.env
# Then start the application
./start-dev.sh
```

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Add your OPENAI_API_KEY

# Create necessary directories
mkdir -p output temp_uploads
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

</details>

## 🎯 Usage

### Web Interface

1. **Access the application**: http://localhost:3000
2. **Choose input method**:
   - Upload a PDF file for automatic text extraction
   - Manually enter book chapters
3. **Configure translation**:
   - Select target language
   - Choose output format (DOCX/PDF)
4. **Monitor progress**: Real-time translation status
5. **Download result**: Professional book-format document

### API Usage

The application provides a REST API for programmatic access:

```bash
# API Documentation
curl http://localhost:8000/docs

# Translate chapters
curl -X POST "http://localhost:8000/api/translation/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "chapters": [{"id": 1, "content": "Chapter content..."}],
    "target_language": "Português"
  }'

# Upload PDF
curl -X POST "http://localhost:8000/api/upload/pdf" \
  -F "file=@book.pdf" \
  -F "target_language=Português" \
  -F "output_format=docx"
```

## 🛠️ Development

### Available Scripts

```bash
./start-dev.sh       # Start both backend and frontend
./start-backend.sh   # Start only backend (port 8000)
./start-frontend.sh  # Start only frontend (port 3000)
./run-tests.sh       # Run all backend tests
./run-tests.sh --unit # Run only unit tests
```

### Project Structure

```
translator/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes
│   │   │   ├── core/           # Configuration & middleware
│   │   │   ├── models/         # Data models
│   │   │   ├── services/       # Business logic
│   │   │   └── utils/          # Utility functions
│   │   ├── tests/              # Test suite
│   │   └── requirements.txt    # Python dependencies
│   ├── frontend/               # React application
│   │   ├── src/
│   │   │   ├── App.tsx         # Main component
│   │   │   ├── api.ts          # API client
│   │   │   └── main.tsx        # Entry point
│   │   └── package.json        # Node.js dependencies
│   ├── docker-compose.yml      # Container orchestration
│   └── setup-project.sh        # Automated setup script
```

### Testing

```bash
# Run all tests
./run-tests.sh

# Run with coverage
./run-tests.sh --coverage

# Run specific test categories
./run-tests.sh --unit
./run-tests.sh --api
./run-tests.sh --e2e
```

## 🐳 Docker Deployment

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your_api_key_here

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the application at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## ⚙️ Configuration

### Environment Variables

Create `backend/.env`:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
PORT=8000
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760  # 10MB
MAX_CHAPTERS=100
OUTPUT_DIR=output
USE_BACKGROUND_TASKS=1
```

### Translation Settings

- **Default Model**: GPT-4 Turbo (better quality)
- **Chunk Size**: 4000 characters (optimal for long content)
- **Temperature**: 0.3 (consistent translations)
- **Concurrent Processing**: Parallel chapter translation

## 📋 Document Specifications

Generated documents follow professional book standards:

- **Page Size**: 6 × 9 inches
- **Typography**: Georgia font, 11pt body text
- **Layout**: Drop caps, right-aligned chapter numbers
- **Pagination**: Alternating left/right page numbers
- **Margins**: Optimized for binding (0.75" inside, 0.5" outside)

## 🔧 Troubleshooting

### Common Issues

**OpenAI API Errors**
```bash
# Check your API key
cat backend/.env | grep OPENAI_API_KEY

# Verify API quota
curl -H "Authorization: Bearer your_api_key" \
  "https://api.openai.com/v1/usage"
```

**Port Conflicts**
```bash
# Check if ports are in use
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# The application will automatically try alternative ports
```

**Dependency Issues**
```bash
# Clean reinstall
rm -rf backend/venv frontend/node_modules
./setup-project.sh
```

### Performance Optimization

- **Large PDFs**: Break into smaller files (< 10MB)
- **Many Chapters**: Use batch processing API endpoints
- **Memory Usage**: Monitor output directory size
- **API Limits**: Implement custom rate limiting if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`./run-tests.sh`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when backend is running
- **Issues**: Create a GitHub issue with detailed reproduction steps
- **API Reference**: Available at http://localhost:8000/docs

---

Built with ❤️ using FastAPI, React, and OpenAI GPT-4
