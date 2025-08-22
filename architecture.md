# System Architecture

## Overview

The Multi-Agent Jira Card Creation System is a containerized local application that automates the creation of high-quality Jira cards using AI agents. The system follows a microservices-within-container pattern with clear separation between frontend, backend, and AI processing components.

## High-Level Architecture

```mermaid
graph TB
    subgraph "LOCAL DOCKER CONTAINER"
        subgraph "Frontend Layer"
            A[Angular UI<br/>PrimeNG]
            A1[Task Selector]
            A2[Markdown Editor]
            A3[Jira Preview & Validation]
            A --> A1
            A --> A2
            A --> A3
        end
        
        subgraph "Backend Layer"
            B[FastAPI Backend]
            B1[Workflow Engine]
            B2[Agent Orchestrator]
            B --> B1
            B --> B2
        end
        
        subgraph "AI Agent Layer"
            C1[Jr Developer Agent<br/>Question Generation]
            C2[Tech Lead Agent<br/>Answer Generation]
            C3[Jira Card Agent<br/>Card Formatting]
        end
        
        A <--> B
        B2 --> C1
        B2 --> C2
        B2 --> C3
    end
    
    subgraph "External Services"
        D[AWS Bedrock<br/>Sonnet 3.7]
        E[Jira API<br/>Template Clone & Create]
        F[Local Files<br/>tasks.md & logs]
    end
    
    C1 --> D
    C2 --> D
    C3 --> D
    B --> E
    B --> F
```

## Component Details

### Frontend Layer (Angular + PrimeNG)

**Technology Stack:**
- Angular 17+ with standalone components
- PrimeNG UI component library
- ngx-markdown for markdown rendering
- Monaco Editor for code editing

**Core Components:**
1. **Task List Component**
   - Displays parsed tasks from tasks.md
   - Shows status indicators (pending/in-progress/complete)
   - Refresh functionality for task file updates

2. **Workflow Stepper Component**
   - Multi-step process visualization
   - Progress tracking and navigation
   - Error state handling

3. **Markdown Editor Component**
   - Rich markdown editing with syntax highlighting
   - Real-time preview capabilities
   - Validation and formatting tools

4. **Jira Preview Component**
   - Side-by-side template vs generated card comparison
   - Field-by-field difference highlighting
   - Final validation interface

**Services:**
- `TaskService`: Task management and status tracking
- `WorkflowService`: Pipeline orchestration
- `JiraService`: Jira API integration
- `ErrorService`: Global error handling and logging

### Backend Layer (FastAPI)

**Technology Stack:**
- FastAPI for REST API framework
- Pydantic for data validation
- Asyncio for concurrent processing
- Python logging with structured output

**Core Modules:**

1. **Workflow Engine (`workflow/`)**
   ```python
   class WorkflowEngine:
       - manage_task_lifecycle()
       - generate_request_guid()
       - track_pipeline_progress()
       - handle_state_persistence()
   ```

2. **Agent Orchestrator (`agents/`)**
   ```python
   class AgentOrchestrator:
       - initialize_strands_agents()
       - route_agent_requests()
       - handle_agent_responses()
       - manage_agent_lifecycle()
   ```

3. **Task Manager (`tasks/`)**
   ```python
   class TaskManager:
       - parse_tasks_markdown()
       - update_task_status()
       - persist_task_changes()
       - validate_task_format()
   ```

4. **Jira Integration (`jira/`)**
   ```python
   class JiraIntegration:
       - authenticate_with_pat()
       - clone_template_card()
       - clear_specified_fields()
       - create_new_card()
   ```

### AI Agent Layer (Strands SDK)

```mermaid
graph LR
    subgraph "Agent Configuration"
        A[Jr Developer Agent]
        B[Tech Lead Agent]
        C[Jira Card Agent]
    end
    
    subgraph "Tools & Capabilities"
        A1[Question Generator<br/>Requirement Analyzer<br/>File Reader]
        B1[Technical Analyzer<br/>Architecture Advisor<br/>Answer Generator]
        C1[Jira Formatter<br/>Field Mapper<br/>Card Validator]
    end
    
    A --> A1
    B --> B1
    C --> C1
    
    A1 --> D[AWS Bedrock<br/>Sonnet 3.7]
    B1 --> D
    C1 --> D
```

**Agent Architecture:**
Each agent is implemented as a separate Strands agent with specialized tools and prompts.

1. **Jr Developer Agent**
   ```python
   agent_config = {
       "name": "jr-developer",
       "model": "anthropic.claude-3-5-sonnet-v2",
       "system_prompt": jr_developer_prompt,
       "tools": [
           "file_reader",
           "requirement_analyzer",
           "question_generator"
       ]
   }
   ```

2. **Tech Lead Agent**
   ```python
   agent_config = {
       "name": "tech-lead", 
       "model": "anthropic.claude-3-5-sonnet-v2",
       "system_prompt": tech_lead_prompt,
       "tools": [
           "technical_analyzer",
           "architecture_advisor",
           "answer_generator"
       ]
   }
   ```

3. **Jira Card Agent**
   ```python
   agent_config = {
       "name": "jira-card",
       "model": "anthropic.claude-3-5-sonnet-v2", 
       "system_prompt": jira_card_prompt,
       "tools": [
           "jira_formatter",
           "field_mapper",
           "card_validator"
       ]
   }
   ```

## Data Flow Architecture

### Request Processing Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant WE as Workflow Engine
    participant JD as Jr Developer Agent
    participant TL as Tech Lead Agent
    participant JC as Jira Card Agent
    participant J as Jira API
    
    U->>WE: Select Task
    WE->>WE: Generate GUID
    WE->>JD: Process Task
    JD->>WE: Return Questions
    WE->>U: Present Questions for Review
    U->>WE: Approve/Edit Questions
    WE->>TL: Process Questions
    TL->>WE: Return Answers
    WE->>U: Present Answers for Review
    U->>WE: Approve/Edit Answers
    WE->>JC: Generate Jira Card
    JC->>WE: Return Card Draft
    WE->>U: Present Card Preview
    U->>WE: Approve Card
    WE->>J: Clone Template & Create Card
    J->>WE: Return Created Card
    WE->>U: Show Success
```

### Data Models

**Core Data Structures:**

```python
class WorkflowRequest:
    guid: str
    task_id: str
    status: WorkflowStatus
    created_at: datetime
    current_step: str
    
class TaskItem:
    id: str
    content: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime]

class AgentResponse:
    agent_name: str
    request_guid: str
    content: str
    metadata: dict
    processing_time: float

class JiraCard:
    template_key: str
    generated_fields: dict
    cleared_fields: list
    final_payload: dict
```

## External Integration Details

### AWS Bedrock Integration

```mermaid
graph TD
    A[Application] --> B[AWS Session Manager]
    B --> C{Authentication Method}
    C -->|SSO| D[AWS SSO Profile]
    C -->|Keys| E[Access Key + Secret]
    C -->|Session| F[Session Token]
    D --> G[Bedrock Runtime Client]
    E --> G
    F --> G
    G --> H[Sonnet 3.7 Inference Profile]
```

**Authentication:**
- AWS SSO profile support
- Access key/secret key authentication
- Session token handling
- Credential refresh logic

**Request Management:**
```python
class BedrockClient:
    def __init__(self, profile_name: str = None):
        self.session = boto3.Session(profile_name=profile_name)
        self.bedrock = self.session.client('bedrock-runtime')
    
    async def invoke_model(self, model_id: str, payload: dict):
        # Inference profile routing
        # Error handling and retries
        # Response parsing
```

### Jira API Integration

```mermaid
graph TD
    A[Jira Integration] --> B[PAT Authentication]
    B --> C[Template Card Fetch]
    C --> D[Field Analysis]
    D --> E[Clone Card Structure]
    E --> F[Clear Specified Fields]
    F --> G[Populate Generated Content]
    G --> H[Create New Card]
    H --> I[Return Card Details]
```

**Authentication:**
- Personal Access Token (PAT) based
- Token validation and refresh
- Permission verification

**Template Cloning Process:**
```python
class JiraTemplateCloner:
    def clone_card(self, template_key: str, new_content: dict):
        # 1. Fetch template card structure
        # 2. Identify fields to clear vs preserve
        # 3. Apply new content mappings
        # 4. Create new card via API
        # 5. Return created card details
```

**Field Management:**
```python
FIELDS_TO_CLEAR = [
    'customfield_10001',  # Sprint
    'customfield_10002',  # Epic
    'customfield_10003',  # Story Points
    'customfield_10004',  # Due Date
    'assignee',
    'description',
    'summary'
]
```

## Error Handling Strategy

### Error Categories

```mermaid
graph TD
    A[System Errors] --> A1[AWS Credential Failures]
    A[System Errors] --> A2[Network Connectivity]
    A[System Errors] --> A3[Container Resource Limits]
    
    B[Agent Errors] --> B1[Model Inference Failures]
    B[Agent Errors] --> B2[Prompt Processing Errors]
    B[Agent Errors] --> B3[Response Parsing Failures]
    
    C[Integration Errors] --> C1[Jira API Auth Failures]
    C[Integration Errors] --> C2[Template Not Found]
    C[Integration Errors] --> C3[Permission Denied]
    
    D[User Input Errors] --> D1[Invalid Task Format]
    D[User Input Errors] --> D2[Malformed Markdown]
    D[User Input Errors] --> D3[Missing Required Fields]
```

### Error Response Strategy

```python
class ErrorHandler:
    def handle_error(self, error: Exception, context: dict):
        # 1. Log error with GUID and context
        # 2. Classify error type
        # 3. Generate user-friendly message
        # 4. Preserve state for retry
        # 5. Return appropriate HTTP response
```

**No Fallback Policy:**
- System fails fast on any error
- No automatic retries or workarounds
- User must address error before proceeding
- Full error context preserved for debugging

## Deployment Architecture

### Container Structure

```mermaid
graph TD
    subgraph "Multi-Stage Docker Build"
        A[Node.js Alpine<br/>Frontend Build] --> D[Python Slim<br/>Runtime Container]
        B[Python Slim<br/>Backend Build] --> D
        C[Dependencies<br/>& Assets] --> D
    end
    
    subgraph "Runtime Environment"
        D --> E[Port 8080<br/>Frontend]
        D --> F[Port 8000<br/>Backend API]
        D --> G[Volume Mounts<br/>tasks.md, logs/]
    end
```

### Local Development Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  jira-card-creator:
    build: .
    ports:
      - "8080:8080"  # Frontend
      - "8000:8000"  # Backend API
    volumes:
      - ./tasks.md:/app/tasks.md
      - ./logs:/app/logs
    environment:
      - AWS_PROFILE=${AWS_PROFILE}
      - JIRA_PAT=${JIRA_PAT}
      - JIRA_BASE_URL=${JIRA_BASE_URL}
```

## Monitoring and Observability

### Logging Strategy

```mermaid
graph LR
    A[Application Events] --> B[Structured Logger]
    B --> C[Log Levels]
    C --> D[DEBUG: Agent Interactions]
    C --> E[INFO: Workflow Steps]
    C --> F[WARN: Recoverable Errors]
    C --> G[ERROR: System Failures]
    
    B --> H[GUID Correlation]
    H --> I[Request Tracking]
    H --> J[Error Context]
```

```python
import logging
import structlog

logger = structlog.get_logger()

def log_request(guid: str, step: str, data: dict):
    logger.info(
        "workflow_step_completed",
        request_guid=guid,
        step=step,
        processing_time=data.get('duration'),
        status=data.get('status')
    )
```

### Metrics Collection

- Request processing times per agent
- Error rates by category
- User interaction patterns
- Jira card creation success rates

## Security Considerations

### Credential Management
- AWS credentials never logged
- Jira PAT stored in environment variables
- No credential persistence in application state

### Data Privacy  
- Task content processed in memory only
- No sensitive data in logs
- Local-only processing (no cloud data storage)

### API Security
- Rate limiting on Jira API calls
- Input validation and sanitization
- HTTPS enforcement for external calls

## Performance Characteristics

### Expected Performance
- Task processing: 30-60 seconds end-to-end
- Agent response time: 5-15 seconds per agent
- UI responsiveness: <200ms for user interactions
- Memory usage: <512MB under normal load

### Scalability Constraints
- Single-user local deployment
- Sequential task processing
- No horizontal scaling capabilities
- Bounded by AWS Bedrock rate limits