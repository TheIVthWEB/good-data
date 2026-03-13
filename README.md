# Good Data - Marketing Analytics AI

Ask questions about your marketing data in plain English. Get insights, recommendations, and visualizations powered by Claude AI.

![Good Data](https://img.shields.io/badge/version-0.1.0-blue)

## Features

- **Natural Language Queries**: Ask questions like "What's my ROAS by channel?"
- **Smart Visualizations**: Auto-generated charts based on your data
- **Marketing Insights**: AI-powered analysis and recommendations
- **Multiple Data Sources**: CSV uploads and Google Sheets integration
- **Correlated Analysis**: Analyze spend, conversions, attribution, and more together

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The app will be available at `http://localhost:3000`

## Usage

1. **Add Data**: Click "Add Data" to upload a CSV or connect Google Sheets
2. **Ask Questions**: Type questions in plain English
3. **Get Insights**: View AI-generated insights, visualizations, and recommendations

### Example Questions

- "What's my total ad spend by campaign?"
- "Which channels have the best ROAS?"
- "Show me daily conversions for the last 30 days"
- "What's the breakdown of spend by source/medium?"
- "Compare CPA across all campaigns"
- "Which campaign has the highest conversion rate?"

## Sample Data

A sample marketing dataset is included at `backend/sample_data/marketing_campaigns.csv` for testing.

## Project Structure

```
good-data/
├── backend/
│   ├── app/
│   │   ├── connectors/     # Data source connectors (CSV, Google Sheets)
│   │   ├── services/       # Business logic (Claude AI, Query processing)
│   │   ├── config.py       # App configuration
│   │   ├── database.py     # SQLite database operations
│   │   ├── models.py       # Pydantic models
│   │   └── main.py         # FastAPI application
│   ├── sample_data/        # Sample datasets
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   └── lib/           # API client utilities
│   └── package.json
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sources` | GET | List all data sources |
| `/api/upload/csv` | POST | Upload a CSV file |
| `/api/connect/sheets` | POST | Connect Google Sheet |
| `/api/query` | POST | Submit a natural language query |
| `/api/schema` | GET | Get combined data schema |

## Google Sheets Setup (Optional)

1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account and download credentials
4. Save as `backend/credentials.json`
5. Share your Google Sheet with the service account email

## Tech Stack

- **Backend**: Python, FastAPI, SQLite, Pandas
- **Frontend**: Next.js, React, Tailwind CSS, Recharts
- **AI**: Claude API (Anthropic)

## License

MIT
