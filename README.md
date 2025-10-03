# Financial Contract Drift Monitor

A comprehensive system for monitoring financial contract changes and detecting drift using Pathway and LandingAI. This system continuously tracks modifications in financial contracts (loan agreements, insurance policies, regulatory filings) and automatically highlights risk-impacting changes.

## 🏗️ Architecture

The system consists of two main components:

### Backend (Python/FastAPI)
- **Pathway**: Live document ingestion and streaming processing
- **LandingAI**: Structured document extraction using ADE DPT-2
- **Drift Detection Engine**: Semantic comparison of contract versions
- **Policy Compiler**: Machine-enforceable rule generation
- **Validation Engine**: Real-time compliance monitoring
- **Webhook System**: External system integration

### Frontend (React/TypeScript)
- **Real-time Dashboard**: Live monitoring interface
- **Interactive Charts**: Data visualization and trends
- **Advanced Filtering**: Search and filter capabilities
- **Detailed Views**: Comprehensive violation analysis
- **Policy Management**: Rule configuration and download

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- LandingAI API key (optional for mock mode)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd HWB
```

### 2. Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys and configuration
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Start Development Environment
```bash
# Start both backend and frontend
./start-dev.sh

# Or start individually:
# Backend: source venv/bin/activate && python main.py
# Frontend: cd frontend && npm run dev
```

### 5. Access the Application
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
HWB/
├── app/                          # Backend application
│   ├── models/                   # Data models
│   ├── services/                 # Business logic
│   ├── api/                      # REST API endpoints
│   └── webhooks/                 # Webhook handlers
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # UI components
│   │   ├── services/             # API integration
│   │   ├── types/                # TypeScript types
│   │   └── lib/                  # Utilities
│   └── package.json
├── uploads/                      # Document upload directory
├── processed/                    # Processed documents
├── streaming_output/             # Pathway streaming output
├── requirements.txt              # Python dependencies
├── main.py                       # Backend entry point
└── start-dev.sh                  # Development startup script
```

## 🔧 Configuration

### Environment Variables (.env)
```ini
# LandingAI Configuration
LANDINGAI_API_KEY=your_landingai_api_key_here
LANDINGAI_BASE_URL=https://api.landing.ai

# Pathway Configuration
PATHWAY_RUNTIME_URL=http://localhost:8080
PATHWAY_API_KEY=your_pathway_api_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/financial_contracts
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your_secret_key_here

# Webhook Configuration
WEBHOOK_SECRET=your_webhook_secret
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/slack/webhook
CRM_WEBHOOK_URL=https://your-crm.com/api/webhooks
```

## 🎯 Key Features

### Document Processing
- **Live Ingestion**: Real-time monitoring of document changes
- **Structured Extraction**: AI-powered field extraction from PDFs
- **Version Comparison**: Semantic diff analysis between versions
- **Evidence Linking**: Direct links to source document pages

### Drift Detection
- **Semantic Analysis**: Understands meaning, not just text changes
- **Risk Assessment**: Prioritizes changes by financial impact
- **Rule Validation**: Checks against machine-enforceable policies
- **Alert Generation**: Real-time notifications for violations

### Dashboard Features
- **Live Monitoring**: Real-time violation updates
- **Interactive Charts**: Visual trend analysis
- **Advanced Filtering**: Search by severity, investor, rule type
- **Detailed Views**: Comprehensive violation analysis
- **Policy Management**: View and download policy packs

## 🔌 API Endpoints

### Core Endpoints
- `GET /health` - System health check
- `GET /contracts` - List all contracts
- `POST /upload` - Upload new contract
- `GET /alerts` - Get violations
- `PATCH /alerts/:id` - Update violation status

### Dashboard Endpoints
- `GET /dashboard/stats` - Dashboard statistics
- `GET /dashboard/violations-timeseries` - Time series data
- `POST /notifications/send` - Send notifications

### Policy Endpoints
- `GET /policies` - List policies
- `POST /policies/compile` - Compile policy rules

## 🛠️ Development

### Backend Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
python main.py

# Run tests
python -m pytest tests/

# Lint code
flake8 app/
```

### Frontend Development
```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

### Adding New Features

1. **Backend**: Add new endpoints in `app/api/`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Integration**: Update API service in `frontend/src/services/api.ts`

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Production Setup
1. Set up PostgreSQL and Redis
2. Configure environment variables
3. Set up reverse proxy (nginx)
4. Enable SSL certificates
5. Configure monitoring and logging

## 📊 Monitoring

### Health Checks
- Backend: `GET /health`
- Frontend: Built-in health monitoring
- Database: Connection status
- External APIs: LandingAI, Pathway status

### Logging
- Structured logging with severity levels
- No secrets logged (security best practice)
- Real-time monitoring dashboard

## 🔒 Security

- **No Secrets in Logs**: All sensitive data loaded from environment
- **API Key Management**: Secure handling of external API keys
- **Input Validation**: Pydantic models for data validation
- **CORS Configuration**: Proper cross-origin resource sharing
- **Rate Limiting**: Protection against abuse

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the Pathway × LandingAI hackathon.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

## 🎉 Acknowledgments

- **Pathway** for real-time streaming capabilities
- **LandingAI** for document extraction technology
- **FastAPI** for the robust backend framework
- **React** and **Tailwind CSS** for the modern frontend