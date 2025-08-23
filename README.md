# Multi-Agent Jira Card Creator

> **Automate Jira card creation with AI-powered repository analysis**  
> Reduce card creation time from 30+ minutes to 3-5 minutes with comprehensive technical analysis

## 🚀 Quick Start

```bash
# 1. Configure environment
cp .env.template .env
# Edit .env with your AWS and Jira credentials

# 2. Start application
./start.sh           # Linux/macOS
# OR
start.bat           # Windows

# 3. Open browser
# http://localhost:4200
```

## 📋 What This Does

This application automatically creates detailed, implementation-ready Jira cards by:

1. **Analyzing** your local repositories (50+ supported)
2. **Understanding** existing code patterns and database schemas  
3. **Generating** technical questions via Junior Developer agent
4. **Providing** expert answers via Tech Lead agent
5. **Creating** comprehensive Jira cards with file references and DB changes

## 🎯 Key Benefits

- **6x Faster**: 3-5 minutes vs 30+ minutes traditional workflow
- **More Comprehensive**: Includes file references, database changes, testing requirements
- **Consistent Quality**: AI analysis ensures nothing is missed
- **Context-Aware**: Understands your existing codebase patterns
- **Human-in-the-Loop**: Review and edit at every step

## 🛠 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Angular UI    │───▶│   FastAPI API    │───▶│  Strands Agents │
│   (Frontend)    │    │   (Backend)      │    │   (AI Engine)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌──────────────────┐    ┌─────────────────┐
         │              │ Repository       │    │ AWS Bedrock     │
         │              │ Scanner          │    │ (Claude 3.7)    │
         │              └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│     Jira        │    │   Oracle DB      │
│ Integration     │    │  (Optional)      │
└─────────────────┘    └──────────────────┘
```

## 📁 Project Structure

```
bl-docs-/
├── README.md                 # This file
├── INSTALLATION.md           # Detailed setup guide  
├── USER_MANUAL.md           # Complete user guide
├── architecture.md          # System architecture
├── .env.template           # Configuration template
├── docker-compose.yml      # Container orchestration
├── start.sh / start.bat    # Startup scripts
├── health-check.sh         # System diagnostics
├── backend/                # FastAPI application
│   ├── main.py            # API endpoints
│   ├── repository/        # Repository scanning
│   ├── database/          # Database connectivity  
│   ├── agents/            # AI agent integration
│   ├── context/           # Workflow context management
│   └── middleware/        # Error handling & validation
└── frontend/              # Angular application
    ├── src/app/
    │   ├── pages/         # Main application pages
    │   ├── components/    # Reusable components
    │   └── services/      # API and validation services
    └── angular.json       # Build configuration
```

## 🏃‍♂️ Quick Commands

```bash
# Start application
./start.sh              # Start with health checks
./restart.sh            # Restart all services
./stop.sh              # Stop all services

# Monitoring
./health-check.sh      # Run diagnostics
./logs.sh              # View logs
./logs.sh -f           # Follow logs in real-time
./logs.sh --errors     # Show only errors

# Access Points
http://localhost:4200  # Dashboard UI
http://localhost:8000  # API backend
http://localhost:8000/docs  # API documentation
```

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# AWS Bedrock (Required)
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1

# Repository Analysis (Required)
REPOSITORIES_PATH=/path/to/your/repositories

# Jira Integration (Required)
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_token

# Database (Optional)
DATABASE_ENABLED=true
DATABASE_JDBC_URL=jdbc:oracle:thin:@localhost:1521:xe
DATABASE_USERNAME=your_db_user
DATABASE_PASSWORD=your_db_password
```

## 📊 Workflow Steps

1. **Task Selection**
   - Architect populates `tasks.md` with task list
   - Developer selects a task from the pre-defined list
   - System creates workflow context automatically

2. **Repository Selection**  
   - Choose relevant repositories from your local collection
   - AI analyzes relevance scores and relationships

3. **Questions Generation**
   - Junior Developer agent generates clarifying questions
   - Review and edit questions for specificity

4. **Answers Generation**
   - Tech Lead agent provides technical implementation guidance  
   - Includes file references and database changes

5. **Jira Card Creation**
   - Final card generated with complete implementation plan
   - Review and create in your Jira instance

## 🎯 Use Cases

### ✅ Perfect For
- **Feature Development**: New functionality requiring multiple files
- **Bug Fixes**: Complex issues spanning multiple repositories
- **Technical Debt**: Refactoring projects with broad impact
- **Integration Tasks**: Connecting systems with database changes
- **API Development**: Backend services with database interactions

### ⚠️ Less Suitable For
- Single-file changes
- Simple configuration updates
- Emergency hotfixes (too thorough for urgent issues)
- Tasks without code implementation

## 📚 Documentation

- **[INSTALLATION.md](INSTALLATION.md)**: Complete setup guide with troubleshooting
- **[USER_MANUAL.md](USER_MANUAL.md)**: Detailed usage guide with best practices  
- **[architecture.md](architecture.md)**: Technical architecture and component details

## 🚦 System Requirements

- **Docker**: 20.10+ with Docker Compose
- **Memory**: 8GB+ RAM (16GB+ recommended)
- **Storage**: 5GB+ free space
- **Network**: Stable internet for AWS Bedrock API
- **Repositories**: Local git repositories (50+ supported)

## 🌟 Success Metrics

You'll know it's working well when:
- Cards created in under 5 minutes
- Implementation details are accurate and actionable
- File references point to real, relevant code
- Database changes are complete with proper SQL
- Developers can implement without additional research

## 🐛 Troubleshooting

**System not starting?**
```bash
./health-check.sh     # Run diagnostics
./logs.sh --errors    # Check error logs
```

**Repository scanning fails?**
- Verify `REPOSITORIES_PATH` in `.env`
- Check directory permissions
- Ensure repositories contain code files

**AI responses generic?**
- Select more relevant repositories
- Write more specific task descriptions  
- Edit questions to be more technical

**Jira integration fails?**
- Verify API token and permissions
- Check Jira URL format
- Test connection manually

## 🤝 Best Practices

### Task Descriptions
- Start with action verbs (implement, fix, add, update)
- Include business context and user impact
- Specify technical requirements and constraints
- Mention integration points with existing systems

### Repository Selection  
- Choose 3-8 highly relevant repositories
- Include core repositories being modified
- Add repositories with similar patterns for context
- Remove low-relevance repositories after analysis

### Quality Assurance
- Review and edit generated questions for specificity
- Enhance answers with additional technical details
- Verify all file references are accurate
- Confirm database changes are complete

## 📈 Performance Tips

- **Repository Organization**: Well-structured, commented code improves AI analysis
- **Selection Strategy**: Quality over quantity for repository selection  
- **Task Scope**: Medium-complexity tasks (1-8 story points) work best
- **Description Detail**: More context leads to better technical analysis

## 🔒 Security & Privacy

- All repository analysis happens locally
- Only relevant patterns sent to AWS Bedrock (never raw code)
- Database connections use read-only access
- API tokens and credentials stored in local `.env` file
- Comprehensive error logging with unique error IDs

---

## 🚀 Ready to 6x Your Productivity?

1. **Setup**: Follow [INSTALLATION.md](INSTALLATION.md) (15 minutes)
2. **Learn**: Read [USER_MANUAL.md](USER_MANUAL.md) (10 minutes)  
3. **Test**: Create your first task (5 minutes)
4. **Scale**: Integrate into team workflow

**Questions?** Check the [USER_MANUAL.md](USER_MANUAL.md) FAQ or run `./health-check.sh` for diagnostics.

---
*Built with FastAPI, Angular, PrimeNG, Strands SDK, and AWS Bedrock Claude 3.7*