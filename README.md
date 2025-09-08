# LLM Knowledge Extractor

## FastAPI-based service for extracting and analyzing knowledge from text using LLMs.

# Setup

## 1. Clone the repository:
```
git clone <repository-url>
cd llm-knowledge-extractor
```

## 2. Copy environment variables provided to a .env file in root directory

## 3. Start the services:
```
docker compose up --build
```

## 4. Run tests (while services are running):
```
docker compose exec web pytest -v
```

## 5.Usage API Endpoints

POST /analyze - Analyze new text
```
curl -X POST "http://localhost:11000/api/v1/text_analyzer/analyze
" \
-H "Content-Type: application/json" \
-d '{"text": "Your text here"}'
```

GET /search - Search analyses by topic or keyword
```
curl "http://localhost:11000/api/v1/text_analyzer/search?topic=technology&limit=10"
```

GET /analysis/{id} - Get specific analysis by ID
```
curl "http://localhost:11000/api/v1/text_analyzer/analysis/{analysis_id}"
```


### Batch Analysis
```
 ~ curl -X POST "http://localhost:11000/api/v1/text_analyzer/analysis/{analysis_id}" \
  -H "Content-Type: application/json" \
  -d '{                                                                  "texts": [
      "Apple Inc. is a technology company based in Cupertino, California.",
      "Tesla is revolutionizing the automotive industry with electric vehicles.",
      "Climate change is one of the most pressing issues of our time."
    ]
  }'
```

### Design Choices

I built the prototype using FastAPI for a lightweight, async-friendly API with clear routing under src/llm_knowledge_extractor/api. Data is persisted with Postgres + SQLAlchemy, managed through Alembic migrations, for reliable storage and schema evolution. The codebase is organized into features (features/text_analyzer), services, DAOs, prompts, schemas, and utils to keep concerns separated and maintainable. A root level notebook to keep track of and experiment with LLM prompts and responses. Docker + Docker Compose streamline local development, while Terraform provides infrastructure-as-code for consistent deployments (terraform config is a very basic starting point setup). 

### Trade-offs

Obviously i was not meant to spend too much time on this, so i focused on the basic structure of how i usually design my Python based AI projects

I implemented batch support using FastAPI background tasks, which works for this prototype but is not as scalable or fault-tolerant as a dedicated task queue like Celery.

The API runs on Uvicorn directly for simplicity, but in production I’d use Gunicorn + Uvicorn workers for better concurrency and stability.

I used a basic noun frequency extractor instead of a full NLP pipeline (e.g., spaCy) to save setup time.

Error handling is minimal — only core cases (empty input, LLM failure) are covered instead of a full validation framework.

I skipped advanced authentication/authorization and exposed endpoints directly for faster delivery.

I included an nginx and ssl certificate folder but did not implement a reverse proxy for routing and static handling because of time constraints.

For deployment, I provided Docker Compose + basic Terraform config, but didn’t implement full CI/CD or cloud integration. Ideally i would seperate environments and services for developement and production

Tests are limited to a few examples, with some external services mocked, a test db would have been ideal; in production, I’d add comprehensive unit and integration coverage with a test db.

