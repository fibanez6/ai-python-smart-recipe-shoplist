# AI Recipe Shoplist Crawler

An intelligent Python 3.11+ application that crawls recipe websites, extracts ingredients using AI, searches multiple grocery stores for the best prices, and generates detailed shopping bills with cost optimization.

## 🚀 Features

- 🤖 **AI-Powered Recipe Extraction**: Uses OpenAI, Azure OpenAI, Ollama, or GitHub Models to intelligently parse recipe websites
- 🛒 **Multi-Store Price Comparison**: Searches Coles, Woolworths, ALDI, and IGA for best prices (mock implementation)
- 🧠 **Smart Optimization**: AI-enhanced price optimization across multiple stores
- 🧾 **Bill Generation**: Creates formatted receipts in PDF, HTML, and JSON formats
- 🌐 **Modern Web Interface**: FastAPI-based web application with responsive design
- 📱 **Mobile-Friendly**: Works seamlessly on desktop and mobile devices
- ⚙️ **Type-Safe Configuration**: Pydantic-based configuration with validation and type checking
- 🔄 **Robust Error Handling**: Automatic retry logic with exponential backoff
- 📊 **Comprehensive Logging**: Structured logging with configurable levels and file output

## 🏗️ Architecture

```
ai-recipe-shoplist/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application
│   ├── models.py                   # Pydantic data models
│   ├── config/
│   │   ├── pydantic_config.py      # Type-safe configuration management
│   │   └── logging_config.py       # Logging configuration
│   ├── services/
│   │   ├── ai_service.py           # AI provider management
│   │   ├── web_fetcher.py          # Web content fetching
│   │   ├── recipe_service.py       # Recipe processing
│   │   └── shopper_service.py      # Shopping optimization
│   ├── ia_provider/
│   │   ├── base_provider.py        # Base AI provider class
│   │   ├── openai_provider.py      # OpenAI implementation
│   │   ├── azure_provider.py       # Azure OpenAI implementation
│   │   ├── ollama_provider.py      # Ollama implementation
│   │   └── github_provider.py      # GitHub Models implementation
│   ├── templates/
│   │   └── index.html             # Web interface
│   └── static/
│       ├── style.css              # Styling
│       └── img/                   # Images
├── .env                          # Environment configuration
├── requirements.txt              # Dependencies
├── pyproject.toml               # Python 3.11+ project config
└── README.md                    # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- pip
- One of the AI providers configured (see AI Provider Setup below)

### Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd ai-recipe-shoplist
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure AI provider:**
   ```bash
   # Create environment file
   cp .env.example .env     # If available, or create new .env file

   # Edit .env with your credentials
   nano .env
   ```

5. **Run the application:**
   
   **Option A: Using the startup script (recommended):**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
   
   **Option B: Direct uvicorn command:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Open your browser:**
   - **Web Interface:** http://localhost:8000
   - **API Documentation:** http://localhost:8000/api/docs
   - **API Re-Documentation:** http://localhost:8000/api/redoc

### Using the Startup Script

The included `start.sh` script provides additional benefits:

- **Automatic environment setup**: Creates virtual environment if missing
- **Dependency management**: Installs/updates requirements automatically  
- **Configuration validation**: Validates your `.env` file before starting
- **Directory creation**: Creates required directories (logs, cache, etc.)
- **Provider checking**: Verifies AI provider connectivity (e.g., Ollama)
- **Flexible configuration**: Reads server host/port from environment variables

```bash
chmod +x start.sh
./start.sh
```

## 🤖 AI Provider Setup

### OpenAI

1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create or edit your `.env` file
3. Set your API key:
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   AI_PROVIDER=openai
   ```

### Azure OpenAI

1. Create Azure OpenAI resource in [Azure Portal](https://portal.azure.com/)
2. Deploy a model (e.g., gpt-4o-mini)
3. Create or edit your `.env` file
4. Configure:
   ```env
   AZURE_OPENAI_API_KEY=your-azure-key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
   AI_PROVIDER=azure
   ```

### Ollama (Local)

1. Install Ollama:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. Start Ollama and pull a model:
   ```bash
   ollama serve
   ollama pull llama3.1
   ```

3. Create or edit your `.env` file
4. Configure:
   ```env
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3.1
   AI_PROVIDER=ollama
   ```

### GitHub Models

1. Request access at [GitHub Models](https://github.com/marketplace/models)
2. Create Personal Access Token with `repo` scope
3. Create or edit your `.env` file
4. Configure:
   ```env
   GITHUB_TOKEN=ghp_your-token-here
   GITHUB_MODEL=gpt-4o-mini
   AI_PROVIDER=github
   ```

## 🌐 Usage

### Web Interface

1. **Navigate to http://localhost:8000**
2. **Enter a recipe URL** from supported sites:
   - AllRecipes.com
   - Food.com  
   - BBC Good Food
   - Any recipe site with structured data
3. **Click "Process Recipe"** to extract ingredients
4. **Review optimization results** showing best prices across stores
5. **Generate bills** in PDF, HTML, or JSON format

### API Endpoints

The application provides a RESTful API:

- `GET /` - Web interface
- `POST /api/process-recipe` - Extract recipe from URL
- `POST /api/optimize-shopping` - Complete optimization pipeline
- `POST /api/generate-bill` - Create shopping bill
- `GET /api/demo` - Load demo recipe
- `GET /api/stores` - List available stores
- `GET /api/docs` - API documentation

### Demo Mode

Try the demo with a sample recipe:
```bash
curl -X POST "http://localhost:8000/api/demo"
```

Or click "Try Demo" in the web interface.

## 🔧 Configuration

The application uses **Pydantic Settings** for type-safe configuration management with automatic environment variable loading and validation.

### Environment Variables

Create a `.env` file in the project root with your configuration:

```env
# =================================================================
# AI PROVIDER CONFIGURATION
# =================================================================
AI_PROVIDER=openai                    # AI provider (openai, azure, ollama, github)

# =================================================================
# OPENAI CONFIGURATION
# =================================================================
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.1
OPENAI_TIMEOUT=30

# =================================================================
# AZURE OPENAI CONFIGURATION  
# =================================================================
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment

# =================================================================
# OLLAMA CONFIGURATION
# =================================================================
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT=30

# =================================================================
# GITHUB MODELS CONFIGURATION
# =================================================================
GITHUB_TOKEN=ghp_your-github-token
GITHUB_MODEL=gpt-4o-mini
GITHUB_API_URL=https://models.inference.ai.azure.com

# =================================================================
# WEB FETCHER CONFIGURATION
# =================================================================
FETCHER_TIMEOUT=30                    # Request timeout in seconds
FETCHER_MAX_SIZE=10485760            # Max content size (10MB)
FETCHER_USER_AGENT=Mozilla/5.0 (compatible; AI-Recipe-Crawler/1.0)
FETCHER_CACHE_TTL=3600               # Cache TTL in seconds
FETCHER_AI_MAX_LENGTH=8000           # Max content length for AI

# =================================================================
# SERVER CONFIGURATION
# =================================================================
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# =================================================================
# LOGGING CONFIGURATION
# =================================================================
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs/app.log
DEBUG_ENABLED=false

# =================================================================
# RETRY CONFIGURATION
# =================================================================
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=60.0

# Provider-specific retry settings
OPENAI_MAX_RETRIES=3
GITHUB_MAX_RETRIES=3
GITHUB_RPM_LIMIT=15                  # GitHub has strict rate limits
```

### Configuration Features

- **Type Safety**: All configuration values are validated and type-checked
- **Environment Variables**: Automatic loading from `.env` files
- **Validation**: Invalid values are caught early with clear error messages
- **Documentation**: Each setting includes description and default values
- **Organized Sections**: Configuration grouped by functionality
- **Backward Compatibility**: Maintains same variable names as before

### Configuration Access

The configuration system provides both modern Pydantic access and backward-compatible exports:

```python
# Modern Pydantic access
from app.config.pydantic_config import settings
print(settings.openai.api_key)
print(settings.web_fetcher.timeout)

# Backward-compatible access (recommended for existing code)
from app.config.pydantic_config import OPENAI_API_KEY, FETCHER_TIMEOUT
print(OPENAI_API_KEY)
print(FETCHER_TIMEOUT)
```

### Store Configuration

Currently uses mock adapters for demonstration. For production:

1. Replace mock adapters in `app/services/store_crawler.py`
2. Implement real store APIs or web scrapers
3. Add store API keys to environment variables

## 🧪 Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black app/ tests/
isort app/ tests/
```

### Type Checking

```bash
mypy app/
```

### Adding New Features

1. **New Recipe Sites**: Extend web fetching and parsing in `web_fetcher.py`
2. **New AI Providers**: Implement `BaseAIProvider` in `ia_provider/` directory
3. **New Configuration**: Add settings to `pydantic_config.py` with proper validation
4. **New Services**: Create new services in `services/` directory with proper logging

## 📊 Optimization Strategies

The system uses multiple optimization strategies:

1. **Single Store**: Find cheapest single store option
2. **Multi-Store**: Optimize across all stores (may require multiple trips)
3. **AI-Enhanced**: Use AI to consider quality, travel costs, and substitutions

The AI optimizer considers:
- Product quality and brand reputation
- Travel costs between stores
- Bulk buying opportunities  
- Suitable ingredient substitutions

## 🎯 Example Workflow

1. **Input**: `https://allrecipes.com/recipe/123/chicken-stir-fry`
2. **AI Extraction**: 
   - Chicken breast (2 pieces)
   - Mixed vegetables (2 cups)
   - Soy sauce (3 tbsp)
   - Rice (1 cup)
3. **Store Search**:
   - Coles: Chicken $8.99, Vegetables $4.50, Soy sauce $3.20, Rice $2.80
   - Woolworths: Chicken $9.50, Vegetables $4.20, Soy sauce $3.50, Rice $2.90
   - ALDI: Chicken $7.99, Vegetables $3.80, Soy sauce $2.90, Rice $2.50
4. **Optimization**: Mix of ALDI (cheaper) + travel costs vs single store
5. **Bill Generation**: PDF receipt with itemized costs and store breakdown

## 🚀 Deployment

### Docker

```bash
docker build -t ai-recipe-shoplist .
docker run -p 8000:8000 --env-file .env ai-recipe-shoplist
```

### AWS Lambda

Use AWS SAM for serverless deployment:

```bash
sam build
sam deploy --guided
```

### Traditional Server

```bash
# Production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Create Pull Request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Quick Fixes

**Application won't start - Missing pydantic_settings module:**
```bash
pip install --upgrade pip
pip install pydantic-settings>=2.0.0
```

**Or reinstall all dependencies:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Common Issues

**Missing Dependencies (pydantic_settings)**
- If you see `ModuleNotFoundError: No module named 'pydantic_settings'`, run:
  ```bash
  pip install --upgrade pip
  pip install pydantic-settings>=2.0.0
  ```
- Or reinstall all dependencies:
  ```bash
  pip install -r requirements.txt --force-reinstall
  ```

**AI Service Not Working**
- Verify API keys are correct
- Check internet connection for cloud providers
- For Ollama, ensure service is running: `ollama serve`

**Rate Limiting (429 Too Many Requests)**
- GitHub Models has strict rate limits (15 requests/minute)
- The app includes automatic retry logic with exponential backoff
- Configure rate limiting settings in your `.env` file:
  ```env
  GITHUB_RPM_LIMIT=15        # Requests per minute (default: 15)
  GITHUB_MAX_RETRIES=3       # Number of retries (default: 3)
  GITHUB_BASE_DELAY=1.0      # Base delay in seconds (default: 1.0)
  GITHUB_MAX_DELAY=60.0      # Maximum delay in seconds (default: 60.0)
  ```
- Consider switching to OpenAI or Azure for higher rate limits
- For production, implement request queuing to stay within limits

**No Products Found**
- Currently using mock data - this is expected
- Implement real store APIs for production use

**Bill Generation Fails**
- Install ReportLab: `pip install reportlab`
- Check file permissions in `generated_bills/` directory

**Web Interface Not Loading**
- Ensure templates and static directories exist
- Check FastAPI is serving static files correctly

### Getting Help

1. Check the [API documentation](http://localhost:8000/api/docs) when running
2. Review application logs for detailed error messages  
3. Try the demo mode to verify setup: `curl -X POST "http://localhost:8000/api/demo"`

## 🔮 Roadmap

- [ ] Real grocery store API integration
- [ ] Machine learning for better ingredient matching
- [ ] Multi-currency support
- [ ] Nutritional information integration
- [ ] User accounts and favorites
- [ ] Mobile app development
- [ ] Meal planning features
- [ ] Integration with shopping list apps

## 🆕 Recent Updates

### v2.0 - Modern Configuration & Type Safety
- **Pydantic Settings**: Migrated from manual environment variable handling to type-safe Pydantic configuration
- **Enhanced Validation**: All configuration values are now validated with clear error messages
- **Organized Structure**: Configuration grouped into logical sections (AI providers, web fetcher, logging, etc.)
- **Better Documentation**: Each setting includes descriptions and sensible defaults
- **Improved Error Handling**: Robust retry logic with exponential backoff for all AI providers
- **Code Cleanup**: Removed outdated test files and consolidated configuration management

---

Built with ❤️ and AI in Python 3.11+