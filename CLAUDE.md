# CLAUDE.md - AI Assistant Guidelines

This document provides essential context and guidelines for AI assistants working with the **good-data** repository.

## Project Overview

**Good Data** is a marketing analytics web application that allows users to ask questions about their marketing data in plain English. It uses Claude AI to convert natural language to SQL, generate insights, and recommend visualizations.

### Key Features

- Natural language to SQL conversion
- Multi-source data support (CSV, Google Sheets)
- AI-powered marketing insights and recommendations
- Auto-generated visualizations
- Marketing metrics analysis (ROAS, CPA, CTR, etc.)

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI, SQLite, Pandas |
| Frontend | Next.js 14, React, Tailwind CSS, Recharts |
| AI | Claude API (Anthropic) |

---

## Repository Structure

```
good-data/
├── backend/
│   ├── app/
│   │   ├── connectors/          # Data source connectors
│   │   │   ├── csv_connector.py
│   │   │   └── sheets_connector.py
│   │   ├── services/            # Business logic
│   │   │   ├── claude_service.py  # AI interactions
│   │   │   └── query_service.py   # Query processing
│   │   ├── config.py            # Settings & env vars
│   │   ├── database.py          # SQLite operations
│   │   ├── models.py            # Pydantic models
│   │   └── main.py              # FastAPI app & routes
│   ├── sample_data/             # Test datasets
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Main chat interface
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx  # Message display
│   │   │   ├── DataSourcePanel.tsx
│   │   │   └── Visualization.tsx
│   │   └── lib/
│   │       └── api.ts           # API client
│   ├── package.json
│   └── tailwind.config.ts
├── CLAUDE.md
├── README.md
└── .gitignore
```

---

## Development Workflow

### Running Locally

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sources` | GET | List data sources |
| `/api/upload/csv` | POST | Upload CSV file |
| `/api/connect/sheets` | POST | Connect Google Sheet |
| `/api/sources/{id}` | DELETE | Remove data source |
| `/api/sources/{id}/refresh` | POST | Refresh data |
| `/api/query` | POST | Submit NL query |
| `/api/schema` | GET | Get data schema |

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes |
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | Path to Google credentials | No |
| `DATABASE_URL` | SQLite path (default: `sqlite:///./data/app.db`) | No |

---

## Code Conventions

### Python (Backend)

- Use type hints for function parameters and returns
- Follow PEP 8 style guidelines
- Use Pydantic models for request/response validation
- Keep services stateless where possible

### TypeScript (Frontend)

- Use functional components with hooks
- Keep components focused and composable
- Use the API client (`lib/api.ts`) for all backend calls
- Use Tailwind for styling (no separate CSS files)

### File Naming

- Python: `snake_case.py`
- TypeScript/React: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Config files: lowercase (`package.json`, `tailwind.config.ts`)

---

## AI Assistant Guidelines

### Key Files to Understand

1. `backend/app/services/claude_service.py` - Claude API integration
2. `backend/app/services/query_service.py` - Query orchestration
3. `backend/app/connectors/` - Data source handling
4. `frontend/src/app/page.tsx` - Main UI component
5. `frontend/src/lib/api.ts` - API client types and functions

### When Modifying

1. **Backend changes**: Test with `uvicorn` running, check `/docs` for Swagger UI
2. **Frontend changes**: Hot reload via `npm run dev`
3. **Claude prompts**: Located in `claude_service.py` - tune for better results
4. **New data sources**: Add connector in `backend/app/connectors/`

### What to Avoid

- Don't hardcode API keys (use `.env`)
- Don't modify database schema without migration plan
- Don't add heavy dependencies without justification
- Don't commit `data/` directory contents

### Marketing Domain Knowledge

The app handles these marketing metrics:
- **CTR** (Click-through rate): clicks / impressions * 100
- **CPC** (Cost per click): spend / clicks
- **CPA** (Cost per acquisition): spend / conversions
- **ROAS** (Return on ad spend): revenue / spend
- **CPM** (Cost per mille): spend / impressions * 1000

Common dimensions: campaign, channel, source, medium, date

---

## Testing

### Manual Testing

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Upload `backend/sample_data/marketing_campaigns.csv`
4. Try example queries from the UI

### Test Queries

```
What's my total spend by campaign?
Which channel has the best ROAS?
Show me daily conversions
Compare CPA across campaigns
What's the trend in CTR over time?
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Ensure backend is running on port 8000 |
| "No data sources" | Upload a CSV first |
| SQL errors | Check Claude prompt in `claude_service.py` |
| Google Sheets 403 | Share sheet with service account email |

---

## Git Conventions

### Commit Messages

```
feat(backend): add new data connector
fix(frontend): handle empty query results
docs: update README with setup instructions
```

### Branches

- `main`: Stable production code
- `claude/*`: AI-assisted development branches
- `feature/*`: Manual feature branches

---

*Last updated: 2026-03-13*
