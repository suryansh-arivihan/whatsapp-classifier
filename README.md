# WhatsApp Educational Query Classifier API

A FastAPI-based classification system for educational AI assistants operating on WhatsApp. The system intelligently classifies incoming student queries, determines subject and language, and routes them to appropriate handlers.

## Features

- **Multi-language Support**: Automatically detects and translates Hindi/Hinglish queries to English
- **Subject Detection**: Identifies academic subjects (Physics, Chemistry, Mathematics, Biology)
- **6 Main Categories**: Classifies queries into subject_related, app_related, complaint, guidance_based, conversation_based, exam_related_info
- **Exam Sub-classification**: Further classifies exam queries into faq, pyq_pdf, asking_PYQ_question, asking_test, asking_important_question
- **Docker Support**: Fully containerized for easy deployment
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`

## Project Structure

```
whatsapp-service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── subject_language_detector.py
│   │   ├── main_classifier.py
│   │   ├── exam_classifier.py
│   │   ├── translator.py
│   │   └── classification_pipeline.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   └── logging_config.py      # Centralized logging
│   └── utils/
│       ├── __init__.py
│       └── exceptions.py          # Custom exceptions
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized deployment)
- OpenAI API Key

### Local Development Setup

1. **Clone the repository**
```bash
cd whatsapp-service
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. **Run the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

### Docker Setup

1. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

2. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

The API will be available at http://localhost:8000

3. **Stop the service**
```bash
docker-compose down
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ORG_ID=your_openai_org_id_here

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## API Usage

### Endpoints

#### 1. Root Endpoint
```
GET /
```

Returns API information and available endpoints.

#### 2. Health Check
```
GET /health
```

Returns service health status.

#### 3. Classification Endpoint
```
POST /classify
```

Classifies an educational query.

**Request Body:**
```json
{
  "message": "What is Newton's first law?",
  "metadata": {
    "user_id": "user123"
  }
}
```

**Response:**
```json
{
  "classification": "subject_related",
  "sub_classification": null,
  "subject": "Physics",
  "language": "English",
  "original_message": "What is Newton's first law?",
  "translated_message": null,
  "confidence_score": 0.85,
  "processing_time_ms": 1250.5,
  "timestamp": "2025-11-13T10:30:00Z"
}
```

### Example Requests

#### Example 1: Subject-related Query (English)
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain the concept of force in physics"
  }'
```

#### Example 2: Exam-related Query (Hindi)
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Physics ke important questions batao"
  }'
```

#### Example 3: App-related Query
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I access the NEET batch?"
  }'
```

## Classification Categories

### Main Categories

1. **subject_related**: Academic questions about concepts, formulas, or problem-solving
2. **app_related**: Questions about app features, navigation, pricing, subscriptions
3. **complaint**: Expressions of dissatisfaction or reported problems
4. **guidance_based**: Study planning, motivation, career guidance
5. **conversation_based**: Casual greetings and social interactions
6. **exam_related_info**: Exam patterns, schedules, PYQ requests, important questions

### Exam Sub-Categories

(Only for queries classified as `exam_related_info`)

1. **faq**: General exam information and syllabus questions
2. **pyq_pdf**: Complete previous year exam paper requests
3. **asking_PYQ_question**: Topic-specific previous year questions
4. **asking_test**: Test series and mock test requests
5. **asking_important_question**: Expected questions for upcoming exams

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Tests

```bash
pytest
```

### Code Style

The project follows PEP 8 guidelines. Format code using:

```bash
black app/
```

### Adding New Features

1. Create new services in `app/services/`
2. Define Pydantic models in `app/models/schemas.py`
3. Add new routes in `app/api/routes.py`
4. Update configuration in `app/core/config.py` if needed

## Monitoring and Logging

Logs are written to stdout and can be viewed using:

```bash
# Docker
docker-compose logs -f classifier-api

# Local
# Logs appear in console
```

## Performance

- P50 Response Time: < 1 second
- P90 Response Time: < 2 seconds
- P99 Response Time: < 3 seconds

## Troubleshooting

### Common Issues

1. **OpenAI API Error**
   - Verify your API key is correct in `.env`
   - Check your OpenAI account has available credits

2. **Port Already in Use**
   - Change the port in `.env` or `docker-compose.yml`
   - Or stop the service using that port

3. **Docker Build Fails**
   - Ensure Docker is running
   - Try `docker-compose build --no-cache`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.
