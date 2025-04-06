# Knowledge Base Agent Documentation

This directory contains comprehensive documentation for the Knowledge Base Agent project.

## 📚 How to Use This Documentation

Start by reading the [index.md](index.md) file, which provides an overview of all available documentation resources.

The documentation is organized into different sections:

- **Architecture**: Design of the system components
- **Components**: Details of specific modules
- **Guides**: How-to instructions
- **API Reference**: Technical reference

## 🔑 Key Documents

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture/overview.md) | High-level system design and data flow |
| [Getting Started](guides/getting_started.md) | Setting up and using the system |
| [Development Tracking](guides/development_tracking.md) | How to track development progress |
| [RAG+KG Query Agent](components/query_agent.md) | Details of the hybrid query system |

## 🚀 Development Plan

The [DEVELOPMENT_PLAN_SOTA.md](../DEVELOPMENT_PLAN_SOTA.md) file in the project root is the central reference for all development activities. Always check it before making code changes.

To get a quick summary of the development status, run:

```bash
python -m src.knowledge_base_agent.scripts.check_plan
```

## 📝 Contributing to Documentation

1. Follow the existing structure and formatting
2. Update documentation whenever you make code changes
3. Use clear, concise language
4. Include code examples where appropriate
5. Reference specific files or classes when describing functionality

## 🔄 Document Generation

Some documentation files might be generated automatically from code comments. 
Please do not edit these files directly, but update the source code comments instead.

## 📊 Documentation Status

The current documentation focuses on:

- Core architecture and design
- RAG+KG query system
- Development process and tracking
- Basic usage guides

Future documentation improvements are planned for:

- Storage schema details
- Performance optimization techniques
- Advanced configuration options
- API reference

## 📋 Documentation Checklist

When implementing a feature, ensure you update the relevant documentation:

1. Update task status in DEVELOPMENT_PLAN_SOTA.md
2. Update component documentation if you modify a specific component
3. Update guides if the usage pattern changes
4. Review the architecture documentation if system design changes 

## 🚀 Documentation Improvements

The documentation in this project has been significantly improved with:

1. **Structured Directory Organization**:
   - `architecture/`: System design and architecture diagrams
   - `components/`: Detailed documentation for specific modules
   - `guides/`: How-to guides for setup, usage, and development
   - `api-reference/`: Command and function references

2. **Development Plan Integration**:
   - Clear links between documentation and development plan
   - Scripts to check development status
   - Git hooks to remind about plan updates

3. **Detailed Component Documentation**:
   - RAG+KG Query Agent documentation with flow diagrams
   - Architecture overview with comprehensive data flow explanation
   - Getting started guide with step-by-step instructions

4. **Process Guidance**:
   - Development tracking guide with status indicators
   - Documentation README with contribution guidelines
   - Git hooks to automate documentation checks

5. **Helper Scripts**:
   - `check_plan.py`: Analyzes development plan status
   - `check_docs.py`: Finds relevant documentation for components
   - `install_hooks.py`: Sets up Git hooks for development workflow 