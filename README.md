# Cerberus 🐕🐕🐕

**AI Agent Platform for Business Automation**

Cerberus is a three-headed guardian for your back-office operations. It deploys AI agents that automate tedious tasks like email management, data entry, and document processing.

## Features

### Email Manager Agent
- Auto-categorize incoming emails (urgent, work, personal, newsletters, etc.)
- Draft responses for your approval
- Extract action items from emails
- Schedule follow-ups
- Daily inbox summaries

### Data Entry Agent
- Extract data from PDFs, images, and documents
- Populate spreadsheets automatically
- Validate data against rules
- Watch folders for new files
- Transform data between formats

### Document Processor Agent
- Summarize long documents
- Extract key information (dates, names, amounts)
- Auto-file documents to correct folders
- Generate reports from multiple documents
- Deep document analysis

## Quick Start

```bash
# Check status
python ~/cerberus/cerberus.py status

# List agents
python ~/cerberus/cerberus.py list

# Run an agent
python ~/cerberus/cerberus.py run --agent email_manager --task "summarize inbox"

# Run demos
python ~/cerberus/demos/run_all_demos.py
```

## Configuration

Agents are configured via YAML files in `~/cerberus/agents/`:

- `email_manager.yaml` - Email categorization rules, templates
- `data_entry.yaml` - Watch folders, field mappings, validation
- `doc_processor.yaml` - Filing categories, summary preferences

## Architecture

Cerberus is built on top of the ai-orchestrator platform, leveraging:
- **Smart Router** - Intelligent model selection
- **APEX Engine** - Complex task decomposition
- **Computer Control** - Browser and native app automation
- **Memory System** - Persistent context and learning

## Directory Structure

```
~/cerberus/
├── cerberus.py           # Main platform class
├── agents/               # Agent implementations
│   ├── base.py           # Base agent class
│   ├── email_manager.py  # Email automation
│   ├── data_entry.py     # Data extraction
│   └── doc_processor.py  # Document processing
├── demos/                # Demo scripts
└── data/                 # Output data
```

## Pricing (Agency Model)

| Tier | Price | What You Get |
|------|-------|--------------|
| Starter | $500 | 1 agent (email or data entry) |
| Pro | $2,000 | Custom agent + 3 integrations + 30 days support |
| Enterprise | $5,000+ | Multi-agent system + ongoing maintenance |

## Contact

For custom agents or enterprise solutions, get in touch.

---

Built with 🐕 by the Cerberus team
