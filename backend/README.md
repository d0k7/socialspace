# SocialSpace Agent 🚀

> Unified AI-powered social media management platform built on Hive framework

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📋 Project Overview

**SocialSpace Agent** is a production-grade AI agent that manages your presence across **12 social media platforms** from a single unified interface.

### Supported Platforms (12)

| Category | Platforms |
|----------|-----------|
| **Messaging** | WhatsApp, Telegram, Discord, WeChat |
| **Social** | Facebook, Instagram, Snapchat, LinkedIn |
| **Content** | YouTube, TikTok, Pinterest |
| **Discussion** | Reddit, Twitter/X |

### Key Features

✅ **Unified Interface** - Manage all platforms from one dashboard  
✅ **AI-Powered** - Intelligent message classification and reply generation  
✅ **Human-in-the-Loop** - Review before sending  
✅ **Self-Improving** - Learns from your communication style  
✅ **Production-Ready** - FAANG-level code quality  

---

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│   Web Dashboard (React)              │
│   - Command Center                   │
│   - Activity Feed                    │
│   - Approval Queue                   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   Hive Agent Backend                 │
│   ┌────────────────────────────┐    │
│   │  Platform Router           │    │
│   └──────────┬─────────────────┘    │
│              │                       │
│    ┌─────────┼─────────┐            │
│    ▼         ▼         ▼            │
│  [WhatsApp][Instagram][Twitter]...  │
└──────────────────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │   Platforms  │
        └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/socialspace-agent.git
cd socialspace-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up Hive framework
# Clone Hive separately
cd ..
git clone https://github.com/adenhq/hive.git
cd hive
pip install -e core

# 5. Return to project
cd ../socialspace-agent/backend

# 6. Install in development mode
pip install -e .

# 7. Run verification tests
python verify_models.py
```

### Configuration

Create a `.env` file:

```env
# API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Platform Credentials
WHATSAPP_API_KEY=your_whatsapp_key
TELEGRAM_BOT_TOKEN=your_telegram_token
# ... add other platform keys
```

---

## 📁 Project Structure

```
socialspace-agent/
├── backend/
│   ├── socialspace_agent/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── unified_message.py    # Core data model
│   │   ├── platforms/
│   │   │   ├── base_platform.py      # Base adapter
│   │   │   ├── whatsapp/
│   │   │   ├── instagram/
│   │   │   └── ... (12 platforms)
│   │   ├── nodes/
│   │   │   ├── fetch/
│   │   │   ├── classify/
│   │   │   ├── generate/
│   │   │   └── send/
│   │   ├── exceptions.py             # Exception hierarchy
│   │   └── agent.py                  # Main agent
│   ├── tests/
│   ├── requirements.txt
│   └── setup.py
├── frontend/
│   └── src/
├── docs/
└── README.md
```

---

## 💻 Development

### Session 1 Completed ✅

**Date:** February 6, 2026  
**Location:** Mumbai, India

**What We Built:**
1. ✅ Complete project structure
2. ✅ Exception hierarchy (FAANG-level error handling)
3. ✅ UnifiedMessage model (works for all 12 platforms)
4. ✅ Comprehensive validation
5. ✅ Test suite
6. ✅ Documentation

**Files Created:**
- `requirements.txt` - All dependencies
- `setup.py` - Package configuration
- `.gitignore` - Git ignore rules
- `exceptions.py` - Exception hierarchy (14 exception classes)
- `models/unified_message.py` - Core data model
- `verify_models.py` - Verification script
- `test_core_models.py` - Comprehensive test suite
- `README.md` - This file

### Running Tests

```bash
# With pytest (recommended)
pytest tests/ -v --cov=socialspace_agent

# Simple verification (no pytest needed)
python verify_models.py
```

---

## 📊 Code Quality

We follow FAANG-level standards:

- ✅ **Type Hints** - Full typing coverage
- ✅ **Docstrings** - Every function documented
- ✅ **Validation** - Pydantic models with validation
- ✅ **Error Handling** - Comprehensive exception hierarchy
- ✅ **Testing** - 90%+ code coverage target
- ✅ **Formatting** - Black code formatter
- ✅ **Linting** - Flake8 + mypy

```bash
# Format code
black socialspace_agent/

# Type checking
mypy socialspace_agent/

# Linting
flake8 socialspace_agent/
```

---

## 🎯 Roadmap

### Phase 1: Foundation (Week 1-2) ✅
- [x] Project structure
- [x] Core models
- [x] Exception handling
- [x] Initial tests

### Phase 2: WhatsApp Integration (Week 3-4)
- [ ] WhatsApp platform adapter
- [ ] Message fetching
- [ ] Message sending
- [ ] Full test coverage

### Phase 3: Multi-Platform (Week 5-8)
- [ ] Telegram adapter
- [ ] Instagram adapter
- [ ] Twitter adapter
- [ ] Platform router

### Phase 4: Frontend (Week 9-10)
- [ ] React dashboard
- [ ] Command center
- [ ] Activity feed
- [ ] Approval queue

### Phase 5: Production (Week 11-12)
- [ ] Deployment setup
- [ ] Monitoring
- [ ] Documentation
- [ ] Launch!

---

## 🤝 Contributing

This is a learning project following FAANG-level practices.

**Development Process:**
1. One session per day
2. Build section by section
3. Test everything
4. Document thoroughly

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 👨‍💻 Author

**Dheeraj Mishra**
- GitHub: [@yourusername](https://github.com/d0k7)
- LinkedIn: [Your Profile](https://linkedin.com/in/dheeraj-mishra-535784249/)
- Email: githubdheerajmishra@gmail.com

---

## 🙏 Acknowledgments

- Built on [Hive Framework](https://github.com/adenhq/hive)
- Inspired by FAANG engineering practices
- Community feedback and support

---

**Built with ❤️ in Mumbai, India 🇮🇳**
