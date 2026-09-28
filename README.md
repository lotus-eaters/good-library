# Good Library

A Goodreads-style reading platform with AI-powered search and recommendations. Track what you read, 
shelve books, rate them, set a yearly reading goal, and get personalized suggestions.

Built with **React 19 + TypeScript** on the frontend and a layered **FastAPI** backend.

## Features

- **Google OAuth login** with JWT-based sessions
- **Shelves and ratings** to organize and score your books
- **Yearly reading challenge** with goal tracking
- **Hybrid book search** that combines keyword lookup with semantic search
- **AI book summaries** and personalized "why recommended" explanations
- **Reading-pattern insights** generated from your activity
- **Genre-affinity recommendations** with a swappable strategy pattern

## Tech stack

| Layer | Tools |
| --- | --- |
| Frontend | React 19, TypeScript, Nginx |
| Backend | FastAPI, Pydantic, Alembic |
| Database | PostgreSQL with pgvector |
| Cache | Redis (tiered TTLs) |
| AI | Groq API (Llama 3.1), fastembed (BAAI bge-small, 384-dim embeddings) |
| Infra | Docker, Docker Compose |

## How it works

**Hybrid search.** Queries run as a keyword lookup and as a semantic search over 384-dimension embeddings stored in PostgreSQL via pgvector. 
Results from both are combined, so exact titles and vague descriptions both work.

**Recommendations.** A genre-affinity engine scores books against your reading history. The scoring logic sits behind a 
swappable strategy interface, so new recommendation approaches can be added without touching the API layer.

**AI features with fallbacks.** Summaries, "why recommended" text, and reading insights 
come from Llama 3.1 through the Groq API. If the AI service is unavailable, the app degrades gracefully and still serves search, shelves, and ratings.

**Caching.** Redis caches search and AI-summary responses with tiered TTLs to keep responses fast and API costs low.

**Backend layout.** The API is layered so routing, business logic, and data access stay separate. Schema changes are managed with Alembic migrations.

## Getting started

Requires Docker and Docker Compose.

```bash
git clone https://github.com/lotus-eaters/good-library.git
cd good-library
cp .env.example .env
# fill in your Google OAuth credentials, JWT secret, and Groq API key in .env
docker compose up --build
```

This starts PostgreSQL (with pgvector), Redis, the FastAPI backend, and the React frontend served through Nginx.


## Project structure

```
good-library/
├── backend/            # FastAPI app, models, migrations
├── frontend/           # React + TypeScript app
├── docker-compose.yml
└── .env.example
```

## Author
Mrunalini M. Backend engineer. [GitHub](https://github.com/lotus-eaters)
