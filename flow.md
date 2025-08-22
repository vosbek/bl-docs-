# Workflow Flow Documentation

## Overview

This document describes the detailed workflow for the Multi-Agent Jira Card Creation System. The system processes tasks through a sequential pipeline of AI agents, with human validation at each step.

## High-Level Flow Diagram

```mermaid
flowchart TD
    START([Application Start]) --> LOAD[Load tasks.md]
    LOAD --> PARSE[Parse Task List]
    PARSE --> DISPLAY[Display Available Tasks]
    DISPLAY --> SELECT{User Selects Task}
    
    SELECT --> MARK[Mark Task In-Process]
    MARK --> GUID[Generate Request GUID]
    GUID --> JR[Jr Developer Agent]
    
    JR --> Q_GEN[Generate Questions]
    Q_GEN --> Q_REVIEW[User Reviews Questions]
    Q_REVIEW --> Q_EDIT{Edit Questions?}
    Q_EDIT -->|Yes| Q_MODIFY[Modify Questions]
    Q_MODIFY --> Q_REVIEW
    Q_EDIT -->|No| TL[Tech Lead Agent]
    
    TL --> A_GEN[Generate Answers]
    A_GEN --> A_REVIEW[User Reviews Answers]
    A_REVIEW --> A_EDIT{Edit Answers?}
    A_EDIT -->|Yes| A_MODIFY[Modify Answers]
    A_MODIFY --> A_REVIEW
    A_EDIT -->|No| JC[Jira Card Agent]
    
    JC --> C_GEN[Generate Card Draft]
    C_GEN --> TEMPLATE[Select Template Card]
    TEMPLATE --> CLONE[Clone Template]
    CLONE --> CLEAR[Clear Fields]
    CLEAR --> POPULATE[Populate Generated Content]
    POPULATE --> PREVIEW[Show Card Preview]
    
    PREVIEW --> APPROVE{User Approves?}
    APPROVE -->|No| EDIT_CARD[Edit Card]
    EDIT_CARD --> PREVIEW
    APPROVE -->|Yes| SUBMIT[Submit to Jira]
    
    SUBMIT --> SUCCESS{Jira Success?}
    SUCCESS -->|No| ERROR[Show Error with GUID]
    ERROR --> RETRY{Retry?}
    RETRY -->|Yes| EDIT_CARD
    RETRY -->|No| SELECT
    
    SUCCESS -->|Yes| COMPLETE[Mark Task Complete]
    COMPLETE --> UPDATE[Update tasks.md]
    UPDATE --> SELECT
```

## Detailed Step-by-Step Process

### Phase 1: Application Initialization

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Angular UI
    participant BE as Backend
    participant FS as File System
    
    U->>UI: Launch Application
    UI->>BE: Initialize System
    BE->>FS: Load tasks.md
    FS->>BE: Return Task Content
    BE->>BE: Parse Tasks
    BE->>UI: Return Task List
    UI->>U: Display Task Dashboard
```

**Steps:**
1. **Application Startup**
   - Docker container initializes
   - Backend services start
   - Frontend loads and connects to API

2. **Task File Loading**
   - Read tasks.md from file system
   - Parse markdown format
   - Extract individual tasks
   - Determine task status (pending/in-progress/complete)

3. **UI Initialization**
   - Display task list with status indicators
   - Show refresh button for task file updates
   - Enable task selection interface

### Phase 2: Task Selection and Processing

```mermaid
stateDiagram-v2
    [*] --> TaskList: Load Tasks
    TaskList --> TaskSelected: User Selection
    TaskSelected --> InProgress: Mark In-Process
    InProgress --> JrDeveloper: Generate GUID
    JrDeveloper --> QuestionReview: Agent Complete
    QuestionReview --> TechLead: Questions Approved
    TechLead --> AnswerReview: Agent Complete
    AnswerReview --> JiraCard: Answers Approved
    JiraCard --> CardPreview: Agent Complete
    CardPreview --> JiraSubmit: Card Approved
    JiraSubmit --> Complete: Success
    Complete --> TaskList: Update Status
    
    QuestionReview --> QuestionEdit: User Edits
    QuestionEdit --> QuestionReview: Save Changes
    
    AnswerReview --> AnswerEdit: User Edits
    AnswerEdit --> AnswerReview: Save Changes
    
    CardPreview --> CardEdit: User Edits
    CardEdit --> CardPreview: Save Changes
    
    JiraSubmit --> Error: API Failure
    Error --> CardEdit: Retry with Edits
    Error --> TaskList: Abandon Task
```

### Phase 3: Jr Developer Agent Processing

```mermaid
flowchart TD
    START([Task Selected]) --> GUID[Generate Request GUID]
    GUID --> LOG[Log Request Start]
    LOG --> PREP[Prepare Agent Context]
    PREP --> CALL[Call Jr Developer Agent]
    
    subgraph "Agent Processing"
        CALL --> ANALYZE[Analyze Task Requirements]
        ANALYZE --> IDENTIFY[Identify Ambiguities]
        IDENTIFY --> GENERATE[Generate Clarifying Questions]
        GENERATE --> FORMAT[Format as Markdown]
    end
    
    FORMAT --> VALIDATE[Validate Response]
    VALIDATE --> ERROR_CHECK{Parsing Error?}
    ERROR_CHECK -->|Yes| ERROR[Log Error with GUID]
    ERROR_CHECK -->|No| SAVE[Save Questions]
    
    ERROR --> RETRY{User Retry?}
    RETRY -->|Yes| CALL
    RETRY -->|No| ABANDON[Abandon Workflow]
    
    SAVE --> PRESENT[Present to User]
```

**Jr Developer Agent Behavior:**
- Reads task description carefully
- Identifies missing technical specifications
- Generates 5-10 specific questions
- Focuses on implementation details
- Outputs structured markdown format

**Example Questions Generated:**
```markdown
## Developer Questions

1. Which Java version and build tool should the SDK target (Maven vs Gradle)?
2. What GraphQL schema introspection endpoint format do the nf-graphql services expose?
3. Should the SDK include client-side caching mechanisms or connection pooling?
4. What authentication mechanism should the SDK support for the GraphQL endpoints?
5. Should the SDK be published to a public repository (Maven Central) or private artifact repository?
```

### Phase 4: User Question Review

```mermaid
flowchart TD
    RECEIVE[Receive Generated Questions] --> DISPLAY[Display in Markdown Editor]
    DISPLAY --> USER_ACTION{User Action}
    
    USER_ACTION -->|Edit| MODIFY[Modify Questions]
    USER_ACTION -->|Add| ADD[Add New Questions]
    USER_ACTION -->|Remove| DELETE[Remove Questions]
    USER_ACTION -->|Approve| VALIDATE[Validate Content]
    
    MODIFY --> SAVE[Save Changes]
    ADD --> SAVE
    DELETE --> SAVE
    SAVE --> PREVIEW[Update Preview]
    PREVIEW --> USER_ACTION
    
    VALIDATE --> ERROR_CHECK{Valid Markdown?}
    ERROR_CHECK -->|No| ERROR_MSG[Show Validation Error]
    ERROR_MSG --> USER_ACTION
    ERROR_CHECK -->|Yes| PROCEED[Proceed to Tech Lead]
```

### Phase 5: Tech Lead Agent Processing

```mermaid
flowchart TD
    START([Questions Approved]) --> CONTEXT[Build Agent Context]
    CONTEXT --> CALL[Call Tech Lead Agent]
    
    subgraph "Agent Processing"
        CALL --> READ[Read Questions]
        READ --> RESEARCH[Research Technical Solutions]
        RESEARCH --> ANALYZE[Analyze Architecture Options]
        ANALYZE --> ANSWER[Generate Detailed Answers]
        ANSWER --> FORMAT[Format with Examples]
    end
    
    FORMAT --> VALIDATE[Validate Response]
    VALIDATE --> SAVE[Save Answers]
    SAVE --> PRESENT[Present to User]
```

**Tech Lead Agent Behavior:**
- Analyzes each question thoroughly
- Provides detailed technical answers
- Includes code examples when relevant
- References best practices and patterns
- Explains architectural decisions

**Example Answers Generated:**
```markdown
## Developer Answers

### Question 1: Which Java version and build tool should the SDK target?
**Answer**: Target Java 11+ with Maven for broader compatibility. The GraphQL Java libraries have excellent Maven support and most enterprise environments can handle Java 11+.

**Code Example**: 
```xml
<dependency>
    <groupId>com.graphql-java</groupId>
    <artifactId>graphql-java-tools</artifactId>
    <version>5.2.4</version>
</dependency>
```

**Best Practices**: Use Maven's dependency management for consistent builds across environments.
```

### Phase 6: User Answer Review

```mermaid
flowchart TD
    RECEIVE[Receive Generated Answers] --> DISPLAY[Display in Markdown Editor]
    DISPLAY --> REVIEW[User Reviews Content]
    REVIEW --> ACTION{User Action}
    
    ACTION -->|Add Details| ENHANCE[Add Technical Details]
    ACTION -->|Correct| FIX[Fix Inaccuracies]
    ACTION -->|Clarify| CLARIFY[Add Clarifications]
    ACTION -->|Approve| VALIDATE[Validate Content]
    
    ENHANCE --> SAVE[Save Changes]
    FIX --> SAVE
    CLARIFY --> SAVE
    SAVE --> PREVIEW[Update Preview]
    PREVIEW --> REVIEW
    
    VALIDATE --> PROCEED[Proceed to Jira Card Agent]
```

### Phase 7: Jira Card Agent Processing

```mermaid
flowchart TD
    START([Answers Approved]) --> CONTEXT[Build Card Context]
    CONTEXT --> CALL[Call Jira Card Agent]
    
    subgraph "Agent Processing"
        CALL --> SYNTHESIZE[Synthesize Q&A Content]
        SYNTHESIZE --> STRUCTURE[Structure Card Format]
        STRUCTURE --> CRITERIA[Generate Acceptance Criteria]
        CRITERIA --> TITLE[Create Card Title]
        TITLE --> DESCRIPTION[Build Description]
        DESCRIPTION --> FIELDS[Map Additional Fields]
    end
    
    FIELDS --> VALIDATE[Validate Card Structure]
    VALIDATE --> SAVE[Save Card Draft]
    SAVE --> TEMPLATE_SELECT[Request Template Selection]
```

**Jira Card Agent Behavior:**
- Synthesizes questions and answers into coherent requirements
- Generates clear, actionable title
- Creates structured description with acceptance criteria
- Maps content to appropriate Jira fields
- Ensures testable, measurable criteria

### Phase 8: Jira Template Integration

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Angular UI
    participant BE as Backend
    participant J as Jira API
    
    UI->>U: Request Template Card Key
    U->>UI: Provide Template Key (e.g., PROJ-123)
    UI->>BE: Validate Template
    BE->>J: Fetch Template Card
    J->>BE: Return Template Data
    BE->>BE: Validate Permissions
    BE->>UI: Show Template Summary
    UI->>U: Confirm Template Usage
    U->>UI: Approve Template
    UI->>BE: Proceed with Template
    BE->>BE: Clone Template Structure
    BE->>BE: Clear Specified Fields
    BE->>BE: Populate Generated Content
    BE->>UI: Return Final Card Preview
```

**Template Processing Steps:**
1. **Template Validation**
   - Verify card exists and is accessible
   - Check user permissions
   - Display template summary for confirmation

2. **Field Analysis**
   - Identify fields to preserve (project, components, etc.)
   - Identify fields to clear (sprint, epic, points, etc.)
   - Map generated content to appropriate fields

3. **Card Assembly**
   - Clone template structure
   - Clear specified fields
   - Populate with generated content
   - Preserve organizational settings

### Phase 9: Final Review and Submission

```mermaid
flowchart TD
    PREVIEW[Display Card Preview] --> COMPARE[Show Template vs New]
    COMPARE --> HIGHLIGHT[Highlight Changes]
    HIGHLIGHT --> USER_ACTION{User Action}
    
    USER_ACTION -->|Edit Title| EDIT_TITLE[Edit Title Field]
    USER_ACTION -->|Edit Description| EDIT_DESC[Edit Description]
    USER_ACTION -->|Change Priority| EDIT_PRIORITY[Change Priority]
    USER_ACTION -->|Approve| SUBMIT[Submit to Jira]
    
    EDIT_TITLE --> SAVE_CHANGES[Save Changes]
    EDIT_DESC --> SAVE_CHANGES
    EDIT_PRIORITY --> SAVE_CHANGES
    SAVE_CHANGES --> PREVIEW
    
    SUBMIT --> JIRA_CALL[Call Jira API]
    JIRA_CALL --> SUCCESS{API Success?}
    
    SUCCESS -->|No| ERROR[Display Error]
    ERROR --> LOG_ERROR[Log Error with GUID]
    LOG_ERROR --> RETRY_OPTION[Offer Retry]
    
    SUCCESS -->|Yes| CREATED[Card Created Successfully]
    CREATED --> UPDATE_STATUS[Mark Task Complete]
    UPDATE_STATUS --> UPDATE_FILE[Update tasks.md]
    UPDATE_FILE --> NOTIFY[Notify User of Success]
```

### Phase 10: Error Handling and Recovery

```mermaid
flowchart TD
    ERROR[Error Detected] --> CLASSIFY[Classify Error Type]
    
    CLASSIFY --> SYSTEM_ERROR[System Error]
    CLASSIFY --> AGENT_ERROR[Agent Error]
    CLASSIFY --> INTEGRATION_ERROR[Integration Error]
    CLASSIFY --> USER_ERROR[User Input Error]
    
    SYSTEM_ERROR --> LOG_SYSTEM[Log with Full Context]
    AGENT_ERROR --> LOG_AGENT[Log Agent State]
    INTEGRATION_ERROR --> LOG_INTEGRATION[Log API Response]
    USER_ERROR --> LOG_INPUT[Log Input Validation]
    
    LOG_SYSTEM --> DISPLAY_ERROR[Display User-Friendly Message]
    LOG_AGENT --> DISPLAY_ERROR
    LOG_INTEGRATION --> DISPLAY_ERROR
    LOG_INPUT --> DISPLAY_ERROR
    
    DISPLAY_ERROR --> INCLUDE_GUID[Include Request GUID]
    INCLUDE_GUID --> OFFER_RETRY[Offer Retry Option]
    
    OFFER_RETRY --> RETRY{User Retries?}
    RETRY -->|Yes| PRESERVE_STATE[Preserve Current State]
    RETRY -->|No| ABANDON[Abandon Workflow]
    
    PRESERVE_STATE --> ALLOW_EDIT[Allow Manual Edits]
    ALLOW_EDIT --> RETRY_STEP[Retry Failed Step]
```

**Error Handling Principles:**
- **Fail Fast**: Stop immediately on any error
- **Preserve Context**: Save all state for retry
- **Clear Communication**: Show user-friendly error messages
- **Traceable**: Include GUID for debugging
- **No Fallbacks**: User must address error to proceed

## State Management

### Workflow State Transitions

```mermaid
stateDiagram-v2
    [*] --> Idle: Application Start
    Idle --> TaskSelected: Select Task
    TaskSelected --> ProcessingQuestions: Jr Developer Agent
    ProcessingQuestions --> ReviewingQuestions: Questions Generated
    ReviewingQuestions --> ProcessingAnswers: Questions Approved
    ProcessingAnswers --> ReviewingAnswers: Answers Generated
    ReviewingAnswers --> ProcessingCard: Answers Approved
    ProcessingCard --> ReviewingCard: Card Generated
    ReviewingCard --> SubmittingJira: Card Approved
    SubmittingJira --> Complete: Jira Success
    Complete --> Idle: Task Marked Done
    
    ProcessingQuestions --> Error: Agent Failure
    ProcessingAnswers --> Error: Agent Failure
    ProcessingCard --> Error: Agent Failure
    SubmittingJira --> Error: Jira Failure
    
    Error --> ReviewingQuestions: Retry from Questions
    Error --> ReviewingAnswers: Retry from Answers
    Error --> ReviewingCard: Retry from Card
    Error --> Idle: Abandon Task
```

### Data Persistence Strategy

```mermaid
flowchart TD
    STATE[Current Workflow State] --> MEMORY[In-Memory Storage]
    MEMORY --> GUID[Request GUID Tracking]
    GUID --> STEP[Current Step Data]
    STEP --> AGENT_RESPONSES[Agent Response Cache]
    
    AGENT_RESPONSES --> QUESTIONS[Generated Questions]
    AGENT_RESPONSES --> ANSWERS[Generated Answers]
    AGENT_RESPONSES --> CARD[Generated Card]
    
    STATE --> FILE[File System Persistence]
    FILE --> TASK_STATUS[Task Status Updates]
    FILE --> LOG_FILES[Error Logs]
    FILE --> CONFIG[Configuration Data]
    
    MEMORY --> CLEANUP[Cleanup on Complete]
    FILE --> PERSISTENT[Persistent Storage]
```

## Performance Expectations

### Timing Breakdown

| Phase | Expected Duration | Critical Path |
|-------|------------------|---------------|
| Task Selection | <1 second | UI Interaction |
| Jr Developer Agent | 5-15 seconds | Bedrock API Call |
| Question Review | User-dependent | Human Review |
| Tech Lead Agent | 10-20 seconds | Bedrock API Call |
| Answer Review | User-dependent | Human Review |
| Jira Card Agent | 5-10 seconds | Bedrock API Call |
| Template Processing | 1-3 seconds | Jira API Call |
| Card Review | User-dependent | Human Review |
| Jira Submission | 2-5 seconds | Jira API Call |

**Total End-to-End Time:** 25-55 seconds (excluding human review time)

### Optimization Opportunities

```mermaid
graph TD
    A[Parallel Agent Calls] --> A1[Questions + Template Fetch]
    B[Response Caching] --> B1[Template Structure Cache]
    C[Pre-validation] --> C1[Input Validation Early]
    D[Async Processing] --> D1[Non-blocking UI Updates]
    
    A1 --> FASTER[Faster Processing]
    B1 --> FASTER
    C1 --> FASTER
    D1 --> FASTER
```

This workflow ensures reliable, user-controlled progression through the AI-assisted Jira card creation process while maintaining quality and providing clear error handling at every step.