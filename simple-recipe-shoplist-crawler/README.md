# Recipe Shoplist Crawler

Small Python project that fetches recipe webpages, extracts ingredients and instructions, normalizes ingredient names and quantities, builds a unified shopping list and searches grocery sites (Coles, Woolworths, Aldi) for matching products and prices. It chooses best store combinations and produces a bill with estimated prices and images.

This scaffold provides a working local UI and backend using FastAPI with simple mocked grocery search adapters.

Why this exists
- Quick prototype to assemble recipe ingredients into a shopping list and estimate cost across grocery retailers.

What is included
- FastAPI backend in `app/`
- Simple web UI templates in `app/templates/` and static files in `app/static/`
- Service layers: fetcher, parser, normalizer, shopper, optimizer
- Mock grocery adapters for Coles/Woolworths/Aldi (replaceable with real scrapers or APIs)
- AWS SAM template `samtemplate.yaml` to deploy as a Lambda function behind API Gateway
- `requirements.txt` for dependencies
- `.gitignore`

Quickstart (local)

1. Create a Python 3.13 virtualenv and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run locally with Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
# Open http://localhost:8000 in your browser
```

3. Enter a recipe URL (examples in code) and click Generate to see a populated shopping list with mocked product images and prices.

Deploy with AWS SAM

1. Install and configure AWS CLI, SAM CLI and ensure you have credentials.
2. Package and deploy (example):

```bash
sam validate --template-file samtemplate.yaml --lint
sam build --template-file samtemplate.yaml --use-container
sam deploy --guided
```

Extending to real grocery APIs

- Replace the mock adapters in `app/services/shopper/adapters.py` with real scrapers or SDK calls.
- Improve normalization and unit parsing in `app/services/normalizer.py`.

Notes
- This project is a scaffold and contains simple heuristics and mocks intended for easy extension.
