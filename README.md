# 🧠 DataGovAI - Utah GRS Knowledge Base Agent

A proprietary knowledge base agent developed by the Utah Office of Data Privacy (ODP) for processing and managing Utah's General Retention Schedules (GRS). This system helps government entities efficiently access and understand record retention requirements and related policies.

Copyright © 2025 Utah Office of Data Privacy (ODP). All Rights Reserved.

## 🎯 Overview

| Component | Description |
|-----------|-------------|
| Purpose | Intelligent access to Utah's General Retention Schedules |
| Developer | Utah Office of Data Privacy (ODP) |
| Collaboration | Utah Valley University's Smith College of Engineering and Technology |
| Primary Use | Government records management compliance |
| Technology | RAG-based (Retrieval-Augmented Generation) knowledge system |

## ✨ Features

| Category | Features |
|----------|-----------|
| Interface | • Intelligent chat interface<br>• Clean and intuitive web UI |
| Search | • Advanced RAG-based retrieval<br>• High-accuracy responses<br>• Source citations |
| Processing | • Comprehensive document pipeline<br>• Metadata extraction<br>• Semantic analysis |
| Configuration | • Environment-based setup<br>• Flexible deployment options |

## 🚀 Quick Start

### System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.10+ |
| Database | PostgreSQL 14+ with pgvector |
| Hardware | CUDA-capable GPU (recommended) |
| OS | Linux/macOS/Windows |

### Setup Steps

1. Clone and setup:
```bash
git clone https://github.com/yourusername/DataGovAI.git
cd DataGovAI
python -m venv rag_env
source rag_env/bin/activate  # On Windows: rag_env\Scripts\activate
pip install -r requirements.txt
```

2. Configure:
```bash
cp .env.example .env
# Edit .env with your settings
python scripts/init_db.py
```

3. Run:
```bash
python app.py
# Visit http://localhost:5000
```

## 💬 Usage Examples

| Query Type | Example Questions |
|------------|------------------|
| Retention Periods | "What is the retention period for financial records?" |
| Personnel Files | "How long should we keep employee personnel files?" |
| Audit Records | "What are the disposition requirements for audit records?" |
| Legal Documents | "What is the retention schedule for legal case files?" |

## 📊 Document Categories

| Category | Count | Percentage | Key Document Types |
|----------|--------|------------|-------------------|
| Financial Records | 1,518 | 7.8% | Budget, Payroll, Audit, Tax |
| Administrative & Governance | 791 | 4.1% | Executive, Policies, Minutes |
| Public Services | 763 | 3.9% | City Council, Utilities, Cemetery |
| Personnel Management | 558 | 2.9% | HR, Staff Records, Applications |
| Education & Training | 557 | 2.9% | Student Records, Training |
| Legal & Compliance | 426 | 2.2% | Civil Cases, Criminal Records |
| Records Management | 399 | 2.1% | Archives, File Systems |
| Property & Planning | 365 | 1.9% | Permits, Zoning, Construction |
| Health & Medical | 348 | 1.8% | Medical Records, Healthcare |

## 🔧 Configuration

| Category | Key Settings | Example |
|----------|-------------|----------|
| Database | POSTGRES_CONNECTION | `postgresql://user:pass@localhost:5432/kb` |
| Embeddings | EMBEDDING_MODEL<br>EMBEDDING_DEVICE | `all-mpnet-base-v2`<br>`cuda` |
| Application | FLASK_ENV<br>DEBUG | `development`<br>`True` |

## 📁 Project Structure

```
DataGovAI/
├── app/                # Main application code
│   ├── static/        # CSS, JS, and assets
│   └── templates/     # HTML templates
├── app.py             # Flask application
├── data/              # Document storage
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── tests/             # Test suite
```

## 📚 Documentation

| Category | Location | Content |
|----------|----------|---------|
| Setup | [docs/setup/](docs/setup/) | Installation & configuration |
| API | [docs/api/](docs/api/) | API reference & examples |
| Architecture | [docs/architecture/](docs/architecture/) | System design & components |
| Development | [docs/development/](docs/development/) | Development guidelines |

For detailed development documentation, testing strategies, and implementation details, please refer to the [docs/](docs/) directory.

## 🔒 License

Copyright © 2025 Utah Office of Data Privacy (ODP). All Rights Reserved.

This software is proprietary and confidential. Unauthorized copying, modification, distribution, or use is strictly prohibited.