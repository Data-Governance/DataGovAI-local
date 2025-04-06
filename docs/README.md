# 📚 DataGovAI Documentation

Welcome to the comprehensive documentation for DataGovAI, the Utah Office of Data Privacy's GRS Knowledge Base Agent. This documentation covers both the standard and SOTA (State-of-the-Art) implementations.

## 📑 Documentation Structure

| Category | Description | Key Documents |
|----------|-------------|---------------|
| 🚀 Getting Started | Quick setup and basic usage | - [Quick Start Guide](guides/quick_start.md)<br>- [Environment Setup](ENVIRONMENT_SETUP.md) |
| 🏗️ Architecture | System design and components | - [Architecture Overview](architecture/README.md)<br>- [Component Details](components/README.md) |
| 💡 Knowledge Base | Core KB functionality | - [KB Overview](knowledge_base/README.md)<br>- [Data Models](knowledge_base/data_models.md) |
| 🔧 Development | Development guidelines | - [Development Guide](development/README.md)<br>- [SOTA Implementation](development/sota_implementation.md) |
| 🌐 API Reference | API documentation | - [REST API](api-reference/rest_api.md)<br>- [Python API](api-reference/python_api.md) |
| 📊 Examples | Usage examples | - [Code Examples](examples/README.md)<br>- [Query Examples](examples/queries.md) |

## 🔍 Quick Links

### For Users
- [Installation Guide](guides/installation.md)
- [Configuration Guide](guides/configuration.md)
- [Usage Examples](examples/README.md)
- [Troubleshooting](guides/troubleshooting.md)

### For Developers
- [Development Setup](development/README.md)
- [Architecture Overview](architecture/README.md)
- [API Documentation](api-reference/README.md)
- [Testing Guide](development/testing.md)

### For Administrators
- [Deployment Guide](guides/deployment.md)
- [Monitoring Guide](guides/monitoring.md)
- [Backup & Recovery](guides/backup_recovery.md)

## 🛠️ Core Components

1. **Document Processing**
   - PyMuPDF for PDF extraction
   - NLTK/spaCy for semantic chunking
   - SentenceTransformers for embeddings

2. **Knowledge Storage**
   - PostgreSQL with pgvector
   - Vector store for embeddings
   - Knowledge graph for relationships

3. **Query Processing**
   - Hybrid RAG + KG approach
   - Local LLM integration
   - Advanced semantic search

## 📈 Documentation Updates

| Date | Version | Description |
|------|---------|-------------|
| 2024-04-06 | 2.0.0 | SOTA implementation documentation |
| 2024-04-05 | 1.1.0 | Added comprehensive API docs |
| 2024-04-04 | 1.0.0 | Initial documentation release |

## 💬 Support

For technical support or questions about this documentation:
- Email: support@datagovai.utah.gov
- Internal Wiki: [DataGovAI Support Portal]
- Issue Tracker: [GitHub Issues]

## 📝 License

This documentation and the DataGovAI system are proprietary and confidential to the Utah Office of Data Privacy. All rights reserved.

---

**Note**: Keep the [Progress Log](progress_log.md) updated when making significant changes to the documentation or implementation. 