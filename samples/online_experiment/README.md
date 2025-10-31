# Text Summarization API

A FastAPI-based REST API that provides text summarization using OpenAI's GPT models.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Running the API

Start the server:
```bash
python app.py
```

Or use uvicorn directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Endpoints

### GET /
Health check endpoint.

### POST /summarize
Generate a summary of the provided text.

**Request Body:**
```json
{
  "text": "Your long text to summarize here...",
  "max_length": 150,  // optional, default: 150 words
  "model": "gpt-3.5-turbo"  // optional, default: "gpt-3.5-turbo"
}
```

**Response:**
```json
{
  "summary": "Generated summary text...",
  "original_length": 250,
  "summary_length": 45
}
```

## Example Usage

```bash
curl -X POST "http://localhost:8000/summarize" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of intelligent agents: any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term artificial intelligence is often used to describe machines that mimic cognitive functions that humans associate with the human mind, such as learning and problem solving.",
       "max_length": 50
     }'
```
