# CaRMS Program Explorer (Lite + Analytics)

A production-style data warehouse and analytics platform for CaRMS program data.

## Architecture

```ascii
Raw Data (Excel/Markdown)
       │
       ▼
Dagster ETL  ───▶  PostgreSQL (Data Warehouse)
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          FastAPI           Streamlit
        (REST API)      (Analytics Dashboard)
```

## Tech Stack

- **Language**: Python 3.12
- **Database**: PostgreSQL 16
- **ETL**: Dagster (Asset-based)
- **API**: FastAPI + Pydantic v2 + SQLModel
- **Frontend**: Streamlit + Plotly
- **Infrastructure**: Docker Compose

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Python 3.12 (for local development)

### Setup

1. **Clone the repository** (if not already done)
   ```bash
   git clone <repo_url>
   cd carms-program-explorer-lite
   ```

2. **Prepare Data**
   Ensure the following files are in `data/raw/`:
   - `1503_discipline.xlsx`
   - `1503_program_master.xlsx`
   - `1503_markdown_program_descriptions.zip`

3. **Run Services**
   ```bash
   cd docker
   docker-compose up --build
   ```

   This will start:
   - **Postgres**: localhost:5432
   - **Dagster**: http://localhost:3000
   - **FastAPI**: http://localhost:8000
   - **Streamlit**: http://localhost:8501

### Running ETL

1. Open Dagster UI at http://localhost:3000.
2. Go to **Assets**.
3. Click **Materialize All** to load data from `data/raw` into PostgreSQL.
4. Verify success status in the UI.

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Streamlit Dashboard** | [http://localhost:8501](http://localhost:8501) | Main user interface for analytics and exploration. |
| **FastAPI Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation (Swagger UI). |
| **Dagster UI** | [http://localhost:3000](http://localhost:3000) | ETL orchestration and monitoring. |

## Project Structure

```
.
├── data/
│   └── raw/            # Raw Excel and Zip files
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
├── src/
│   └── carms/
│       ├── api/        # FastAPI application
│       ├── db/         # Database models and engine
│       ├── dashboard/  # Streamlit app
│       ├── etl/        # Dagster assets and resources
│       └── config.py   # Configuration
├── dagster.yaml        # Dagster instance config
├── workspace.yaml      # Dagster workspace config
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Future Improvements

- **Semantic Search**: Implement pgvector to search study program descriptions semantically.
- **Match Simulation**: Integrate matching algorithm engine.
- **Cloud Deployment**: Terraform scripts for AWS (ECS/RDS).
- **Authentication**: Add OAuth2 for API and Dashboard access.
