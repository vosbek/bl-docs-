# Multi-Agent Jira Card Creator - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Creating Your First Task](#creating-your-first-task)
4. [Using the Workflow](#using-the-workflow)
5. [Repository Selection](#repository-selection)
6. [Review and Editing](#review-and-editing)
7. [Jira Integration](#jira-integration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

## Getting Started

### What This Application Does
The Multi-Agent Jira Card Creator is an AI-powered system that automatically generates detailed, implementation-ready Jira cards by analyzing your local repositories and database schemas. It uses a multi-agent approach where different AI agents handle different aspects of the analysis:

- **Junior Developer Agent**: Asks clarifying questions about requirements
- **Tech Lead Agent**: Provides technical analysis and implementation guidance  
- **Jira Card Agent**: Creates comprehensive cards with file references and database changes

### Expected Performance
- **Traditional Workflow**: 30+ minutes per card (manual analysis, research, writing)
- **With This System**: 3-5 minutes per card (automated analysis, human curation)
- **Improvement**: ~6x faster workflow

### Prerequisites
Before using the application, ensure you have:
- ✅ Completed installation (see `INSTALLATION.md`)
- ✅ All repositories checked out locally in a single directory
- ✅ AWS Bedrock access configured
- ✅ Jira API token configured
- ✅ Application running at http://localhost:4200

### Accessing the Application
1. **Start the Application**
   ```bash
   # On Linux/macOS:
   ./start.sh
   
   # On Windows:
   start.bat
   ```

2. **Open Your Browser**
   - Navigate to: http://localhost:4200
   - You should see the dashboard loading

3. **Verify System Status**
   - Check that all indicators in the "System Status" card are green
   - If any are red/yellow, see [Troubleshooting](#troubleshooting)

## Dashboard Overview

### Main Components

#### 1. Task Creation Card (Left Side)
- **Task ID**: Unique identifier for your task (e.g., "PROJ-123", "TEAM-FEATURE-001")
- **Task Type**: Feature, Bug Fix, Technical Debt, or Infrastructure
- **Description**: Detailed description of what needs to be implemented

#### 2. System Status Card (Right Side)
- **API Health**: Backend service status
- **Repository Scanner**: Repository analysis engine status
- **Database**: Database connection status (if configured)
- **AI Agents**: Agent orchestration system status
- **Repositories Found**: Number of repositories discovered

#### 3. Repository Overview Tab (Bottom)
Shows all discovered repositories with:
- Repository name and path
- Primary programming language
- Detected frameworks
- File count and size
- Last scan timestamp

#### 4. System Information Tab (Bottom)
Displays configuration and performance metrics:
- Repository path configuration
- AWS region settings
- Database schema information
- Performance statistics

### Status Indicators
- 🟢 **Green**: System healthy and ready
- 🟡 **Yellow**: System functional with warnings
- 🔴 **Red**: System error requiring attention

## Creating Your First Task

### Step 1: Fill Out the Task Form

#### Task ID Guidelines
- **Format**: Use a consistent pattern like "PROJ-123" or "TEAM-FEATURE-001"
- **Length**: 3-50 characters
- **Characters**: Letters, numbers, dashes, and underscores only
- **Examples**:
  - ✅ "USER-AUTH-001"
  - ✅ "BUG-FIX-LOGIN"
  - ✅ "INFRA_UPGRADE_DB"
  - ❌ "test" (too short)
  - ❌ "My Task!!!" (invalid characters)

#### Task Types
- **Feature**: New functionality or enhancement
- **Bug Fix**: Fixing existing issues
- **Technical Debt**: Refactoring, optimization, code cleanup
- **Infrastructure**: DevOps, deployment, configuration changes

#### Description Best Practices
- **Minimum**: 10 characters (system requirement)
- **Recommended**: 50+ characters for better AI analysis
- **Include**:
  - What needs to be implemented
  - Why it's needed (business context)
  - Any specific requirements or constraints
  - Expected user experience changes

**Example Good Description**:
```
Implement user authentication system with JWT tokens.
Users need to be able to register, login, logout, and reset passwords.
Must integrate with existing user database and support SSO with Google.
Should include rate limiting and account lockout after failed attempts.
```

**Example Poor Description**:
```
Add login stuff
```

### Step 2: Submit the Task
1. Click "Create Task & Start Workflow" button
2. System will validate your input and show any errors/warnings
3. If successful, you'll be redirected to the workflow page
4. A unique context ID will be generated to track your task

### Validation Feedback
The system provides real-time validation:
- **Red errors**: Must be fixed before proceeding
- **Yellow warnings**: Suggestions for improvement (can proceed)

Common validation messages:
- Task ID format requirements
- Description length recommendations
- Suggestions for clearer action words

## Using the Workflow

The workflow consists of 4 main steps, each with human-in-the-loop curation:

### Workflow Overview
```
Task Creation → Repository Selection → Questions & Answers → Jira Card Creation
      ↓                  ↓                    ↓                     ↓
  Your Input    →   AI Analysis    →   AI Dialogue   →    Final Card
```

### Step Navigation
- **Progress Indicator**: Shows current step and completion status
- **Step Names**: Repository Context → Questions → Answers → Jira Card  
- **Navigation**: Steps are sequential (cannot skip ahead)
- **Back Button**: Return to dashboard at any time

## Repository Selection

### Step 1: Repository Context Selection

#### Purpose
Select repositories that are relevant to your task. The AI will analyze these repositories to:
- Understand existing code patterns
- Identify similar implementations
- Find relevant dependencies and frameworks
- Detect database interactions

#### Available Repositories Table
- **Name**: Repository name and local path
- **Primary Language**: Dominant programming language
- **Frameworks**: Detected frameworks and libraries
- **Files**: Number of files in repository
- **Size**: Repository size in MB
- **Last Scanned**: When repository was last analyzed

#### Selection Guidelines

**For New Features**:
- Select repositories that contain similar functionality
- Include any repositories that will be modified
- Consider repositories with shared dependencies

**For Bug Fixes**:
- Select repositories where the bug exists
- Include repositories with related functionality
- Consider repositories that might be affected by the fix

**For Technical Debt**:
- Select all repositories that will be refactored
- Include repositories with similar patterns to standardize
- Consider repositories with dependencies on the code being changed

**Selection Tips**:
- **Minimum**: 1 repository (but consider more for context)
- **Recommended**: 3-8 repositories for comprehensive analysis
- **Maximum**: 20 repositories (more may slow analysis)
- **Quality over Quantity**: Better to select highly relevant repositories than many irrelevant ones

#### Relevance Analysis
After selecting repositories, click "Analyze Relevance" to:
- Score each repository's relevance to your task (0-100%)
- Get recommendations for additional repositories
- See why each repository was deemed relevant
- Remove low-relevance repositories if desired

#### Repository Filters
- **Language Filter**: Show only repositories in specific languages
- **Framework Filter**: Filter by detected frameworks
- **Size Filter**: Filter by repository size
- **Recent Activity**: Show recently updated repositories first

### Proceeding to Next Step
1. Select repositories using checkboxes
2. Click "Analyze Relevance" (optional but recommended)
3. Review relevance scores and adjust selection if needed
4. Click "Proceed to Questions Generation"

## Review and Editing

### Step 2: Questions Generation & Review

#### What Happens
The Junior Developer Agent analyzes your task and selected repositories to generate clarifying questions about:
- Technical implementation details
- Architecture decisions
- Integration requirements
- Testing strategies
- Performance considerations
- Security requirements

#### Questions Review Interface
- **Generated Questions**: List of AI-generated questions
- **Edit Questions**: Click on any question to edit it
- **Add Questions**: Add custom questions using the "Add Question" button
- **Remove Questions**: Delete questions that aren't relevant
- **Reorder Questions**: Drag and drop to prioritize questions

#### Question Quality Indicators
- ✅ **Good Question**: Specific, actionable, relevant to implementation
- ⚠️ **Needs Review**: Generic, vague, or potentially irrelevant
- ❌ **Poor Question**: Too broad, duplicate, or not applicable

#### Editing Tips
- **Be Specific**: Change "How should we handle errors?" to "How should we handle authentication token expiration errors?"
- **Add Context**: Include relevant repository names or file paths
- **Focus on Implementation**: Questions should lead to actionable answers
- **Remove Duplicates**: Consolidate similar questions

#### Example Questions
**Good Questions**:
- "Should the user authentication follow the same JWT pattern as in the user-service repository?"
- "What database migration strategy should we use for the new user_sessions table?"
- "Should we implement the same rate limiting approach used in the api-gateway repository?"

**Questions Needing Improvement**:
- "How should we implement this?" → Too vague
- "What about security?" → Too broad  
- "Any other considerations?" → Not specific

### Step 3: Answers Generation & Review

#### What Happens
The Tech Lead Agent analyzes your task, selected repositories, and approved questions to provide:
- Technical implementation guidance
- Code examples and patterns from your repositories
- Database schema recommendations
- Architecture decisions with justifications
- Testing strategies
- Performance and security considerations

#### Answers Review Interface
- **Generated Answers**: Comprehensive responses to each question
- **Edit Answers**: Modify answers to add context or correct information
- **Add Details**: Expand answers with additional requirements
- **Technical Depth**: Answers include file references and code snippets
- **Implementation Clarity**: Step-by-step guidance for developers

#### Answer Quality Indicators
- ✅ **High Quality**: Specific implementation details with file references
- ⚠️ **Needs Enhancement**: Good guidance but could use more detail
- ❌ **Insufficient**: Too generic or missing key information

#### What Good Answers Include
- **Specific File References**: "Following the pattern in `src/auth/jwt-handler.js`"
- **Database Details**: "Add columns to user_profiles table: session_token (VARCHAR(255)), expires_at (TIMESTAMP)"
- **Code Patterns**: "Use the same validation approach as UserController.validateInput()"
- **Integration Points**: "Update the API gateway configuration in `config/routes.yml`"
- **Testing Strategy**: "Add integration tests following the pattern in `tests/auth/jwt.test.js`"

#### Editing Answers
- **Add Specifics**: Include exact file paths, method names, database table names
- **Clarify Steps**: Break down complex implementations into steps
- **Add Constraints**: Include any business rules or technical limitations
- **Update References**: Ensure all file and repository references are accurate

## Jira Integration

### Step 4: Jira Card Creation

#### What Happens
The Jira Card Agent creates a comprehensive, implementation-ready card including:
- **Title**: Clear, descriptive summary
- **Description**: Detailed implementation plan with markdown formatting
- **Epic**: Suggested epic categorization
- **Labels**: Relevant tags (feature, backend, database, etc.)
- **Story Points**: Estimated complexity (1-21 scale)
- **Implementation Files**: List of files that need to be created/modified
- **Database Changes**: Required schema modifications
- **Testing Requirements**: Testing strategy and files needed

#### Card Preview
- **Full Preview**: See exactly how the card will appear in Jira
- **Markdown Rendering**: Rich formatting with code blocks, lists, tables
- **File References**: Clickable links to implementation files
- **Database Scripts**: SQL statements for schema changes
- **Testing Checklist**: Specific test cases to implement

#### Card Editing
- **Title**: Modify for clarity or project conventions
- **Description**: Add business context or modify technical details
- **Story Points**: Adjust based on team capacity and complexity
- **Labels**: Add project-specific labels or remove irrelevant ones
- **Epic**: Change epic assignment if needed

#### Template Selection
- **Standard Template**: General-purpose card format
- **Feature Template**: Optimized for new features
- **Bug Fix Template**: Includes reproduction steps and testing focus
- **Technical Debt Template**: Emphasizes refactoring and improvement metrics
- **Infrastructure Template**: Includes deployment and monitoring considerations

### Creating the Jira Card
1. **Review** the generated card content
2. **Edit** any sections that need modification
3. **Select Template** appropriate for your task type
4. **Verify** all file references and database changes are accurate
5. **Click "Create Jira Card"** to submit to your Jira instance

### After Creation
- **Jira Link**: Direct link to the created card
- **Card ID**: Jira ticket number (e.g., PROJ-123)
- **Success Confirmation**: Verification that card was created successfully
- **Next Steps**: Suggestions for follow-up actions

## Troubleshooting

### Common Issues and Solutions

#### 1. System Status Issues

**API Health: Error**
```
Symptoms: Red status, dashboard not loading properly
Solutions:
- Run: ./health-check.sh
- Check logs: ./logs.sh backend
- Restart: ./restart.sh
- Verify .env configuration
```

**Repository Scanner: Inactive**
```
Symptoms: No repositories found, scanning fails
Solutions:
- Verify REPOSITORIES_PATH in .env exists
- Check repository directory permissions
- Ensure repositories contain code files
- Run: docker-compose exec backend ls -la /app/repositories
```

**Database: Not Connected**
```
Symptoms: Database features unavailable
Solutions:
- Check DATABASE_JDBC_URL in .env
- Verify database credentials
- Test connection manually
- Review database logs
```

#### 2. Workflow Issues

**Questions Not Generated**
```
Symptoms: Empty questions list, generation fails
Solutions:
- Verify at least one repository is selected
- Check repository contains analyzable code
- Review task description for clarity
- Check AWS Bedrock connectivity
```

**Answers Too Generic**
```
Symptoms: Vague responses, no file references
Solutions:
- Select more relevant repositories
- Edit questions to be more specific
- Add technical details to questions
- Ensure repositories contain related functionality
```

**Jira Card Creation Fails**
```
Symptoms: Error during card creation
Solutions:
- Verify JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env
- Check Jira project permissions
- Test Jira API manually
- Review Jira project configuration
```

#### 3. Performance Issues

**Slow Repository Scanning**
```
Symptoms: Long loading times, timeouts
Solutions:
- Reduce number of repositories
- Exclude large binary files
- Check system resources (memory, disk)
- Increase container memory limits
```

**AI Response Delays**
```
Symptoms: Long waits for questions/answers
Solutions:
- Check AWS Bedrock quota and throttling
- Verify internet connectivity
- Monitor AWS CloudWatch for API errors
- Consider simpler task descriptions
```

### Error Messages

#### Frontend Error Messages
- **"Task ID is required"**: Fill in the Task ID field
- **"Task description must be at least 10 characters long"**: Add more detail
- **"Context ID invalid"**: Session expired, create new task
- **"No repositories selected"**: Choose at least one repository

#### Backend Error Messages
- **"Context manager not initialized"**: System startup issue, restart application
- **"Repository path does not exist"**: Check REPOSITORIES_PATH configuration
- **"AWS credentials not configured"**: Verify AWS settings in .env
- **"Database connection failed"**: Check database configuration

### Getting More Help

#### Log Analysis
```bash
# View all logs
./logs.sh

# View only errors  
./logs.sh --errors

# Follow logs in real-time
./logs.sh -f

# Save logs to file
./logs.sh --save debug.log
```

#### Health Checking
```bash
# Run comprehensive health check
./health-check.sh

# Check specific service
docker-compose ps
docker-compose logs backend
```

#### Configuration Review
```bash
# Review configuration (remove sensitive data before sharing)
cat .env

# Test specific components
curl http://localhost:8000/api/health
curl http://localhost:4200
```

## Best Practices

### Task Creation

#### Writing Effective Task Descriptions
✅ **DO**:
- Start with an action verb (implement, fix, add, update)
- Include business context and user impact
- Specify technical requirements or constraints
- Mention integration points with existing systems
- Include acceptance criteria when possible

❌ **DON'T**:
- Write single-word descriptions
- Use only technical jargon without context
- Skip business justification
- Leave requirements vague or ambiguous

#### Task ID Conventions
- **Project Prefix**: Use consistent project abbreviations
- **Category**: Include feature area (AUTH, API, UI, DB)
- **Number**: Sequential numbering for tracking
- **Examples**: 
  - USER-AUTH-001 (user authentication, task 1)
  - API-RATE-LIMIT (API rate limiting feature)
  - BUG-LOGIN-SESSION (login session bug fix)

### Repository Selection Strategy

#### For Different Task Types

**New Feature Development**:
1. Core repositories that will be modified
2. Repositories with similar existing features  
3. Shared libraries and utilities
4. Integration test repositories

**Bug Fixes**:
1. Repository containing the bug
2. Repositories with dependencies on buggy code
3. Test repositories with relevant test cases
4. Documentation repositories if applicable

**Refactoring/Technical Debt**:
1. All repositories being refactored
2. Repositories with similar patterns to standardize
3. Shared dependencies that might be affected
4. Documentation and configuration repositories

#### Selection Quality Metrics
- **High Relevance** (90-100%): Core implementation repositories
- **Medium Relevance** (50-89%): Supporting or dependent repositories
- **Low Relevance** (0-49%): Consider removing unless specifically needed

### Question and Answer Optimization

#### Effective Questions Focus On:
- **Implementation Specifics**: Exact patterns, file structures, database schemas
- **Integration Points**: How new code connects with existing systems
- **Error Handling**: Specific error conditions and responses
- **Testing Strategy**: What needs to be tested and how
- **Performance Requirements**: Scalability and optimization needs

#### Quality Answers Should Include:
- **File References**: Exact paths to relevant code
- **Code Examples**: Patterns from existing repositories
- **Database Details**: Schema changes with column specifications
- **Step-by-Step Instructions**: Clear implementation sequence
- **Testing Requirements**: Specific test cases and coverage needs

### Jira Card Quality

#### High-Quality Cards Include:
- **Clear Acceptance Criteria**: Specific, measurable outcomes
- **Implementation Plan**: Step-by-step development approach
- **File Change List**: Complete list of files to modify/create
- **Database Migration Scripts**: Exact SQL for schema changes
- **Testing Strategy**: Unit, integration, and manual test requirements
- **Deployment Notes**: Any special deployment considerations

#### Card Organization:
- **Use Headers**: Structure information with H2/H3 headers
- **Bullet Points**: Break down complex requirements
- **Code Blocks**: Format code examples and SQL properly
- **Checklists**: Create actionable todo items
- **Links**: Reference existing documentation or cards

### Team Collaboration

#### Sharing Results
- **Export Cards**: Save card content before creating in Jira
- **Share Context**: Provide context ID for team review
- **Document Decisions**: Note any changes made during review
- **Version Control**: Track iterations and improvements

#### Knowledge Sharing
- **Pattern Documentation**: Document successful patterns for reuse
- **Repository Organization**: Keep repositories well-organized for better AI analysis
- **Naming Conventions**: Use consistent naming for better pattern recognition
- **Code Comments**: Well-commented code improves AI understanding

## FAQ

### General Usage

**Q: How many repositories should I select?**
A: For most tasks, 3-8 repositories provide optimal balance. Include core repositories being modified plus 2-5 repositories with related patterns or dependencies.

**Q: Can I edit the generated content?**
A: Yes! Every step allows editing. Questions, answers, and Jira cards can all be modified to better match your needs and team conventions.

**Q: How long does the process take?**
A: Typically 3-5 minutes total: 30 seconds for questions, 1-2 minutes for answers, 30 seconds for card generation, plus review time.

**Q: Can I save progress and come back later?**
A: Currently, sessions are maintained while the application is running. For longer sessions, complete the workflow in one sitting or restart from the beginning.

### Technical Questions

**Q: What programming languages are supported?**
A: The system analyzes code patterns in any text-based language. It works best with popular languages like JavaScript, Python, Java, C#, Go, TypeScript, etc.

**Q: How does repository analysis work?**
A: The system scans file contents, dependencies, frameworks, and code patterns. It identifies common implementations, database interactions, and architectural patterns.

**Q: Is my code sent to external services?**
A: Code analysis happens locally. Only relevant patterns and abstractions are sent to AWS Bedrock for AI processing, never raw source code.

**Q: Can I use this without Jira?**
A: Yes! You can complete the workflow and copy the generated card content to any project management tool.

### Advanced Usage

**Q: How do I optimize for my team's coding standards?**
A: The AI learns from your repository patterns. Well-organized, consistently-formatted repositories with good comments produce better results.

**Q: Can I customize the agent prompts?**
A: The agent definitions in the `agents/` directory can be modified to match your team's specific needs and terminology.

**Q: How do I handle very large repositories?**
A: Use `.gitignore` patterns to exclude large binary files, generated code, and node_modules. Focus on source code directories.

**Q: Can I integrate with other tools besides Jira?**
A: The generated cards are in markdown format and can be adapted for GitHub Issues, Azure DevOps, Linear, or other tools.

### Troubleshooting

**Q: The AI responses seem generic. How can I improve them?**
A: 1) Select more relevant repositories, 2) Write more specific task descriptions, 3) Edit questions to be more technical, 4) Include implementation constraints in your description.

**Q: Repository scanning is slow. How can I speed it up?**
A: 1) Reduce the number of repositories, 2) Exclude large files via .gitignore, 3) Increase Docker container memory, 4) Run on faster hardware.

**Q: Questions aren't relevant to my task. What should I do?**
A: Edit or replace questions to be more specific to your implementation needs. The system learns from your selected repositories, so ensure they're relevant.

**Q: The Jira card is too detailed/not detailed enough. How do I adjust?**
A: Edit the answers to include more/less implementation detail. More technical answers lead to more detailed cards.

### Business Questions

**Q: What's the ROI of using this system?**
A: Based on typical usage: 30+ minutes saved per card, improved consistency, better technical analysis, and reduced context switching for developers.

**Q: How does this compare to GitHub Copilot or other AI tools?**
A: This system provides end-to-end workflow automation with project-specific analysis, while Copilot focuses on code completion. They complement each other well.

**Q: Can junior developers use this effectively?**
A: Yes! The system provides senior-level technical analysis and implementation guidance, helping junior developers create comprehensive, well-planned tasks.

**Q: How do I measure success with this tool?**
A: Track: time per card creation, card implementation accuracy, developer satisfaction, and reduced back-and-forth during implementation.

---

## Getting Support

### Before Requesting Help
1. Check this user manual
2. Review the installation guide
3. Run the health check script
4. Check application logs
5. Verify your configuration

### Information to Include in Support Requests
- Operating system and version
- Docker version
- Error messages (with error IDs when available)
- Configuration (with sensitive data removed)
- Steps to reproduce the issue
- Output from `./health-check.sh`

### Success Metrics
You know the system is working well when:
- ✅ Cards are created in under 5 minutes
- ✅ Generated content requires minimal editing
- ✅ Implementation details are accurate and specific
- ✅ Database changes are complete and correct
- ✅ File references point to real, relevant code
- ✅ Developers can implement cards without additional research

**Happy automating! 🚀**