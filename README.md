# RAG Project Management System

A memory-enhanced project management system built with RAG (Retrieval-Augmented Generation) technology to help freelance AI consultants track projects, clients, and conversations.

## 🎯 Purpose

This system serves as your **persistent memory** for project management, allowing you to:
- Store and retrieve project information instantly
- Remember client details and preferences across conversations
- Track task progress and project status
- Build institutional knowledge over time
- Enhance Claude conversations with relevant context

## 🚀 Quick Start

1. **Setup**:
   ```bash
   python setup_and_test.py
   ```

2. **Initialize the system**:
   ```bash
   python main.py init
   ```

3. **Add your first document**:
   ```bash
   python main.py ingest /path/to/document.md --doc_type=client_profile
   ```

4. **Search your knowledge base**:
   ```bash
   python main.py search "project status"
   ```

## 📋 Core Features

### Document Management
- **Auto-detection** of document types (client profiles, meeting notes, tasks, etc.)
- **Intelligent chunking** for optimal retrieval
- **Metadata extraction** from content (client names, projects, priorities)
- **Tag extraction** from hashtags and mentions

### Smart Retrieval  
- **Semantic search** using sentence transformers
- **Context-aware** responses based on query intent
- **Client/project filtering** for targeted information
- **Relevance scoring** for result ranking

### Memory Enhancement
- **Conversation logging** for building context over time
- **Automatic context injection** for Claude interactions
- **Project dashboards** showing comprehensive status
- **Client overviews** with interaction history

## 🛠️ CLI Commands

```bash
# System management
python main.py init                    # Initialize system
python main.py status                  # Show system statistics
python main.py types                   # List document types

# Document operations  
python main.py ingest file.md          # Add document
python main.py note "content" "title"  # Quick note
python main.py search "query"          # Search documents

# Project management
python main.py project "ProjectName"   # Project overview
python main.py client "ClientName"     # Client summary  
python main.py recent                  # Recent activities
python main.py context "query"         # Get context for query
```

## 🔧 Architecture

```
rag_system/
├── core/
│   ├── rag_engine.py         # ChromaDB + embeddings
│   ├── document_manager.py   # High-level document operations
│   ├── context_provider.py   # Context retrieval and formatting
│   └── claude_integration.py # Claude conversation enhancement
├── models/
│   └── document.py          # Data models and schemas
├── utils/
│   └── text_processing.py   # Text cleaning and analysis
└── storage/                 # ChromaDB persistence
```

## 📊 Document Types

- **client_profile**: Client information and contacts
- **project_details**: Project specs and requirements  
- **meeting_notes**: Meeting summaries and action items
- **task_update**: Task progress and status updates
- **decision_log**: Important decisions and rationale
- **code_snippet**: Code examples and technical notes
- **template**: Reusable templates and boilerplates
- **conversation**: Chat logs and discussions

## 🧠 How It Enhances Your Work

### Before RAG System:
- ❌ Forget client preferences between conversations
- ❌ Lose track of project status and next steps
- ❌ Repeat questions about past decisions
- ❌ No institutional memory across projects

### With RAG System:
- ✅ **Instant recall** of any project detail
- ✅ **Context-aware** responses in every conversation
- ✅ **Automatic suggestions** for next steps
- ✅ **Knowledge accumulation** that improves over time

## 🔮 Future Enhancements

The system is designed for incremental improvements:

- [ ] Web interface for easier document management
- [ ] Integration with external tools (Slack, GitHub, etc.)
- [ ] Automated report generation
- [ ] Advanced analytics and insights
- [ ] Multi-modal support (images, PDFs, audio)

## 🤝 Integration with Claude

Use `claude_helper.py` for seamless integration:

```python
# Get context for a query
python claude_helper.py context "project status" --client="Acme Corp"

# Save conversation to memory  
python claude_helper.py save-conversation "Planning Session" --project="Website"

# Quick memory addition
python claude_helper.py quick-add "Bug fixed in auth module" "update" "Auth Fix"
```

---

**Built for Claude Code users** - This system transforms Claude from a stateless assistant into a memory-enhanced project management partner. 🚀# planner
