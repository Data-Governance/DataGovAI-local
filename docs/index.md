# Knowledge Base Agent Documentation

Welcome to the Knowledge Base Agent documentation. This central hub provides access to all documentation resources for the project.

## 📖 Overview

The Knowledge Base Agent is a state-of-the-art system for processing, storing, and querying Utah General Retention Schedules (GRS). It features:

- Advanced PDF text extraction
- Semantic chunking for context-aware document segmentation
- High-quality vector embeddings
- Local LLM-powered entity extraction
- RAG+KG query system for accurate answers
- PostgreSQL storage with pgvector extension

## 📚 Documentation Structure

This documentation is organized into four main sections:

### 🏗️ Architecture

- [**Architecture Overview**](architecture/overview.md) - System components and data flow
- [**Storage Design**](architecture/storage.md) - PostgreSQL database schema
- [**Processing Pipeline**](architecture/processing.md) - Document chunking and embedding

### 🧩 Components

- [**RAG+KG Query Agent**](components/query_agent.md) - Hybrid query system
- [**Document Processor**](components/document_processor.md) - Document processing workflow
- [**Entity Extractor**](components/entity_extractor.md) - LLM-based entity extraction
- [**Embedding Service**](components/embedding_service.md) - Vector embeddings

### 📝 Guides

- [**Getting Started**](guides/getting_started.md) - Installation and setup
- [**Development Tracking**](guides/development_tracking.md) - Development plan maintenance
- [**Custom Entities**](guides/custom_entities.md) - Adding new entity types
- [**Troubleshooting**](guides/troubleshooting.md) - Common issues and solutions

### 📎 API Reference

- [**CLI Commands**](api-reference/cli.md) - Command-line interface
- [**Python API**](api-reference/python_api.md) - Using the Python API
- [**REST API**](api-reference/rest_api.md) - HTTP endpoints
- [**Configuration**](api-reference/configuration.md) - Configuration options

## 🚀 Development Plan

The SOTA branch follows the [Development Plan](../DEVELOPMENT_PLAN_SOTA.md), which details:

- Project goals and approach
- Step-by-step implementation plan
- Current status of each component
- Completed and remaining tasks

**Important:** Always check the development plan before making any code changes!

## 💻 External Resources

- [**GitHub Repository**](https://github.com/yourusername/knowledge-base-agent)
- [**Issue Tracker**](https://github.com/yourusername/knowledge-base-agent/issues)
- [**Contributing Guide**](../CONTRIBUTING.md)

## 🔍 Quick Links

| Task | Resource |
|------|----------|
| **Setting up the project** | [Getting Started Guide](guides/getting_started.md) |
| **Processing documents** | [create_knowledge_base.py](../create_knowledge_base.py) |
| **Querying the knowledge base** | [query_knowledge_base.py](../query_knowledge_base.py) |
| **Understanding the query system** | [RAG+KG Query Agent](components/query_agent.md) |
| **Tracking development progress** | [Development Tracking Guide](guides/development_tracking.md) |

## 📊 Project Status

The Knowledge Base Agent project is actively under development. See the [Development Plan](../DEVELOPMENT_PLAN_SOTA.md) for the current status.

Key completed components:
- ✅ Advanced PDF extraction (PyMuPDF)
- ✅ Semantic chunking (NLTK)
- ✅ SentenceTransformer embeddings
- ✅ Enhanced LLM extraction with relationships
- ✅ RAG+KG query system

Current focus areas:
- 🔄 Testing and refinement
- 🔄 Documentation improvements
- 🔄 Performance optimization

## 🤝 Contributing

We welcome contributions to both the code and documentation. Please see the [Contributing Guide](../CONTRIBUTING.md) for details on how to contribute. 