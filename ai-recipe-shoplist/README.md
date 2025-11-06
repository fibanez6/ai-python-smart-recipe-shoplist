# AI Recipe Shoplist Crawler

An intelligent Python 3.11+ application that crawls recipe websites, extracts ingredients using AI, and searches multiple grocery stores for products. This application demonstrates AI-powered recipe analysis and grocery store product matching.

> **📋 Note**: This project is currently under active development. Features and functionality are being continuously improved and expanded.

## 🚀 Features

- 🤖 **AI-Powered Recipe Extraction**: Uses OpenAI, Azure OpenAI, Ollama, or GitHub Models to intelligently parse recipe websites
- 🛒 **Multi-Store Product Search**: Searches Coles, Woolworths, ALDI, and IGA for products based on ingredients
- 🧠 **Smart Product Matching**: AI-enhanced product matching across multiple stores
- 🌐 **Modern Web Interface**: FastAPI-based web application with responsive design
- 📱 **Mobile-Friendly**: Works seamlessly on desktop and mobile devices
- ⚙️ **Type-Safe Configuration**: Pydantic-based configuration with validation and type checking
- 🔄 **Robust Error Handling**: Automatic retry logic with exponential backoff
- 📊 **Comprehensive Logging**: Structured logging with configurable levels and file output

## 📱 Application Screenshots

### Initial Recipe Input Form
<div align="center">
   <img src="doco/img/shopping_list_form.png" alt="Shopping List Form" width="75%">
</div>

*The main interface where users enter a recipe URL to begin the ingredient extraction process.*

### Example Recipe - Gazpacho
<div align="center">
   <img src="doco/img/gazpacho_recipe.png" alt="Gazpacho Recipe" width="50%">
</div>

*Example recipe processing using [Gazpacho from RecipeTin Eats](https://www.recipetineats.com/gazpacho/) - demonstrating AI-powered ingredient extraction from recipe websites.*

### Search Results Display
<div align="center">
   <img src="doco/img/shopping_list_results.png" alt="Shopping List Results" width="75%">
</div>

*Results showing extracted ingredients and matched products from various grocery stores.*

## 🏗️ Architecture

```
ai-recipe-shoplist/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup & routing
│   ├── models.py                   # Pydantic data models
│   ├── api/
│   │   ├── __init__.py            # API package initialization
│   │   └── v1.py                  # API v1 endpoints (versioned API)
│   ├── config/
│   │   ├── pydantic_config.py      # Type-safe configuration management
│   │   ├── logging_config.py       # Logging configuration
│   │   └── store_config.py         # Store configuration management
│   ├── services/
│   │   ├── ai_service.py           # AI provider management
│   │   ├── web_fetcher.py          # Web content fetching
│   │   ├── web_data_service.py     # Web data processing
│   │   ├── grocery_service.py      # Grocery store management
│   │   └── store_crawler.py        # Store crawling services
│   ├── ia_provider/
│   │   ├── base_provider.py        # Base AI provider class
│   │   ├── openai_provider.py      # OpenAI implementation
│   │   ├── azure_provider.py       # Azure OpenAI implementation
│   │   ├── ollama_provider.py      # Ollama implementation
│   │   ├── github_provider.py      # GitHub Models implementation
│   │   └── stub_provider.py        # Stub implementation for testing
│   ├── scrapers/
│   │   └── html_content_processor.py  # HTML content extraction & processing
│   ├── templates/
│   │   └── index.html             # Web interface template
│   ├── static/
│   │   ├── style.css              # Styling
│   │   └── app.js                 # Frontend JavaScript
│   └── utils/
│       ├── ai_helpers.py          # AI utility functions
│       ├── html_helpers.py        # HTML processing utilities
│       └── str_helpers.py         # String processing utilities
├── doco/
│   └── img/                       # Documentation images
├── stub_responses/                # Mock AI responses for testing
├── tests/                         # Test suite
├── .env                          # Environment configuration
├── requirements.txt              # Dependencies
├── pyproject.toml               # Python 3.11+ project config
├── start.sh                     # Startup script
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
   - **API Documentation:** http://localhost:8000/api/v1/docs
   - **API Re-Documentation:** http://localhost:8000/api/v1/redoc

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
3. **Click "Process Recipe"** to extract ingredients using AI
4. **Review extracted ingredients** and search for products in grocery stores
5. **View product matches** across different stores

### API Endpoints

The application provides a RESTful API with **versioned endpoints** for better maintainability and backward compatibility:

#### API v1 Endpoints (`/api/v1/`)
- `GET /` - Web interface
- `GET /health` - Health check endpoint
- `POST /api/v1/process-recipe-ai` - AI-powered recipe processing with shopping plan generation
- `POST /api/v1/search-stores` - Search grocery stores for specific ingredients
- `POST /api/v1/fetcher` - Get web content fetching details
- `GET /api/v1/fetcher-stats` - Get web fetcher cache statistics
- `POST /api/v1/clear-fetcher-cache` - Clear the web fetcher cache
- `POST /api/v1/clear-content-files` - Clear saved content files
- `GET /api/v1/demo` - Load demo recipe data

#### API Documentation
- `GET /api/v1/docs` - Interactive API documentation (Swagger UI)
- `GET /api/v1/redoc` - Alternative API documentation (ReDoc)

#### Legacy Support
- Legacy `/api/*` endpoints automatically redirect to `/api/v1/*` for backward compatibility
- `GET /api/docs` → Redirects to `/api/v1/docs`
- `GET /api/redoc` → Redirects to `/api/v1/redoc`

### Current Functionality

The application currently provides:

1. **Recipe Processing**: Extract ingredients from recipe URLs using AI
2. **Store Integration**: Connect with multiple grocery store configurations (Coles, Woolworths, ALDI, IGA)
3. **Product Matching**: Use AI to match extracted ingredients with store products
4. **Web Interface**: User-friendly interface for recipe input and result display

### Demo Mode

Try the demo with a sample recipe using the v1 API:
```bash
curl -X GET "http://localhost:8000/api/v1/demo"
```

Or use the web interface for an interactive experience.

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
LOG_DEBUG_ENABLED=false

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

The application supports multiple grocery stores with configurable adapters:

- **Coles**: Australian supermarket chain
- **Woolworths**: Australian supermarket chain  
- **ALDI**: International discount supermarket
- **IGA**: Independent Grocers of Australia

Store configurations include:
- Search URL patterns
- HTML selectors for product extraction
- Product page URL patterns
- Store-specific data processing

For production use:
1. Configure store-specific search mechanisms in `app/config/store_config.py`
2. Implement real web scraping or API integration
3. Add store API keys to environment variables if required

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

1. **New API Endpoints**: Add to `app/api/v1.py` for current API or create `app/api/v2.py` for new API version
2. **New Recipe Sites**: Extend web fetching and parsing in `web_data_service.py` and `html_content_processor.py`
3. **New AI Providers**: Implement `BaseAIProvider` in `ia_provider/` directory
4. **New Configuration**: Add settings to `pydantic_config.py` with proper validation
5. **New Services**: Create new services in `services/` directory with proper logging
6. **New Stores**: Add store configurations in `config/store_config.py`
7. **API Versioning**: For breaking changes, create new API version in `app/api/v2.py`

## 📊 Current Implementation

The system currently implements:

1. **AI-Powered Recipe Extraction**: Intelligently extracts ingredients, quantities, and units from recipe websites
2. **Multi-Store Integration**: Connects to multiple grocery store configurations with customizable search patterns
3. **Product Matching**: Uses AI to match extracted ingredients with available store products
4. **Web Interface**: Provides an intuitive interface for recipe processing and result visualization

### Data Flow

1. **Input**: Recipe URL (e.g., `https://allrecipes.com/recipe/123/chicken-stir-fry`)
2. **AI Extraction**: 
   - Chicken breast (2 pieces)
   - Mixed vegetables (2 cups)
   - Soy sauce (3 tbsp)
   - Rice (1 cup)
3. **Store Search**: Query configured stores for matching products
4. **Product Matching**: AI analyzes and matches products to ingredients
5. **Results Display**: Present matched products with store information

### Example Workflow

```python
# 1. Process Recipe URL with AI (v1 API)
POST /api/v1/process-recipe-ai
{
  "recipe_url": "https://allrecipes.com/recipe/123/chicken-stir-fry"
}

# Response: Complete recipe with ingredients and shopping plan
{
  "success": true,
  "data": {
    "url": "https://allrecipes.com/recipe/123/chicken-stir-fry",
    "recipe": {
      "title": "Chicken Stir Fry",
      "ingredients": [...],
      "instructions": [...]
    }
  }
}

# 2. Search Stores for Ingredients (v1 API)
POST /api/v1/search-stores
{
  "ingredients": [
    {"name": "chicken breast", "quantity": 2, "unit": "PIECE"},
    {"name": "mixed vegetables", "quantity": 2, "unit": "CUP"}
  ],
  "stores": ["coles", "woolworths", "aldi"]
}

# 3. View Results
{
  "success": true,
  "stores": [...],
  "products": [...],
  "ia_stats": [...],
  "timestamp": "2025-11-07T10:30:00"
}
```

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
- This indicates the AI product matching didn't find suitable matches
- Check ingredient names are clear and specific
- Verify store configurations are properly set up
- Try different ingredient variations

**Recipe Extraction Fails**
- Ensure the recipe URL is accessible and contains structured recipe data
- Some sites may require specific parsing logic
- Check the AI provider is working correctly with a simple test

**Store Search Issues**
- Verify store configurations in `app/config/store_config.py`
- Check if the stores are accessible and responding
- Review logs for specific error messages during store searches

**Web Interface Not Loading**
- Ensure templates and static directories exist
- Check FastAPI is serving static files correctly
- Verify all dependencies are installed

### Getting Help

1. Check the [API documentation](http://localhost:8000/api/v1/docs) when running
2. Review application logs for detailed error messages  
3. Try the demo mode to verify setup: `curl -X GET "http://localhost:8000/api/v1/demo"`

## 🔮 Roadmap

- [ ] Real grocery store API integration and web scraping
- [ ] Price comparison and optimization algorithms
- [ ] Shopping cart and bill generation features
- [ ] Machine learning for better ingredient matching
- [ ] Multi-currency support
- [ ] Nutritional information integration
- [ ] User accounts and favorites
- [ ] Mobile app development
- [ ] Meal planning features
- [ ] Integration with shopping list apps
- [ ] Bulk purchasing recommendations
- [ ] Store location and proximity optimization

## 🆕 Recent Updates

### v2.2 - Modular Architecture & API Versioning
- **Modular API Structure**: Separated API endpoints into versioned modules (`app/api/v1.py`)
- **API Versioning**: Implemented proper API versioning with `/api/v1/` endpoints
- **Backward Compatibility**: Legacy `/api/` endpoints automatically redirect to `/api/v1/`
- **Clean Architecture**: Main application (`main.py`) now focused on setup and routing
- **Better Code Organization**: API logic separated from application configuration
- **Improved Maintainability**: Easier to add future API versions (v2, v3, etc.)
- **Updated Documentation**: API docs now available at `/api/v1/docs` and `/api/v1/redoc`

### v2.1 - Enhanced Grocery Store Integration
- **Multi-Store Support**: Added support for Coles, Woolworths, ALDI, and IGA with configurable search patterns
- **Improved Product Matching**: Enhanced AI-powered product matching across multiple stores
- **Store Configuration**: Flexible store configuration system with HTML selectors and search patterns
- **Web Data Service**: New service layer for web content fetching and processing
- **Better Error Handling**: Improved error handling for store searches and product matching

### v2.0 - Modern Configuration & Type Safety
- **Pydantic Settings**: Migrated from manual environment variable handling to type-safe Pydantic configuration
- **Enhanced Validation**: All configuration values are now validated with clear error messages
- **Organized Structure**: Configuration grouped into logical sections (AI providers, web fetcher, logging, etc.)
- **Better Documentation**: Each setting includes descriptions and sensible defaults
- **Improved Error Handling**: Robust retry logic with exponential backoff for all AI providers
- **Code Cleanup**: Removed outdated test files and consolidated configuration management

---

Built with ❤️ and AI in Python 3.11+