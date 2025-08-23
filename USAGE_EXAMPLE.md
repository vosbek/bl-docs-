# Multi-Agent Jira Card Creator - Usage Example

## Real Example: Processing a Task from tasks.md

Let's walk through a complete example using one of your actual tasks.

### Step 1: Architect Populates tasks.md

Your `tasks.md` file contains:
```markdown
# Tasks
* Create a Github action that will auto build a Java SDK used for building type safe graphql clients against the nf-graphql services.  It should be able to point to a given environment when building and should be kicked off manually on the nf-graphql-subgraph-template repository whenever we want a new SDK generated.
* Remove the top level shadowDom and fix styling issues due to this from imedia-header-mfe.
* Remove the top level shadowDom and fix styling issues due to this from imedia-firelight-mfe.
```

### Step 2: Developer Opens Dashboard

When you open http://localhost:4200, the dashboard shows:

**Available Tasks from tasks.md**
```
ID | Task Description                                                    | Status      | Actions
1  | Create a Github action that will auto build a Java SDK...         | Not Started | [Process Task]
2  | Remove the top level shadowDom and fix styling issues from...     | Not Started | [Process Task]  
3  | Remove the top level shadowDom and fix styling issues from...     | Not Started | [Process Task]
```

**Task Summary:**
- Total: 26 tasks
- Not Started: 26
- In Progress: 0  
- Completed: 0

**Task Categories:**
- GitHub Actions (1)
- MFE (Micro-frontend) (9)
- Pipeline Migration (9)
- Java/Backend (2)
- Launch Darkly (2)
- Database (1)
- GraphQL (2)

### Step 3: Developer Selects a Task

Developer clicks **"Process Task"** on Task #1 (GitHub Actions task).

**System Response:**
- Creates context ID: `7f3e9a2b-4c5d-4e6f-8a9b-1c2d3e4f5g6h`
- Auto-generates task ID: `TASK-001`
- Determines task type: `infrastructure` (based on keywords "GitHub action", "deployment")
- Updates task status to "In Progress"
- Redirects to workflow page

### Step 4: Repository Selection

**Workflow Page Shows:**
```
Task: TASK-001 - Infrastructure
Description: Create a Github action that will auto build a Java SDK used for building type safe graphql clients against the nf-graphql services...
```

**Available Repositories (example):**
```
Name                              | Language | Frameworks        | Files | Size
nf-graphql-services              | Java     | Spring Boot       | 234   | 45MB
nf-graphql-subgraph-template     | Java     | GraphQL, Maven    | 89    | 12MB  
java-sdk-commons                 | Java     | Maven, JUnit      | 156   | 23MB
github-actions-templates         | YAML     | GitHub Actions    | 45    | 2MB
type-safe-clients                | Java     | CodeGen, Jackson  | 78    | 8MB
```

**Developer selects:**
- ✅ nf-graphql-services (contains the GraphQL schema)
- ✅ nf-graphql-subgraph-template (target repository)  
- ✅ java-sdk-commons (common SDK patterns)
- ✅ github-actions-templates (existing action patterns)

### Step 5: AI Analysis & Questions

**Junior Developer Agent generates questions:**

1. **"Should the GitHub Action follow the same build pattern as in `github-actions-templates/.github/workflows/maven-build.yml`?"**

2. **"What environment parameter should be used to point to different GraphQL endpoints? Should it follow the pattern in `nf-graphql-services/config/environments.properties`?"**

3. **"Should the generated SDK follow the same packaging structure as `java-sdk-commons/src/main/java/com/company/sdk/`?"**

4. **"Which GraphQL schema files from `nf-graphql-services/src/main/resources/graphql/` should be included in the SDK generation?"**

5. **"Should the action trigger follow the manual dispatch pattern from `github-actions-templates/.github/workflows/manual-deploy.yml`?"**

6. **"What artifact naming convention should be used? Follow the pattern `sdk-{service-name}-{version}-{environment}.jar`?"**

### Step 6: Developer Reviews Questions

Developer edits for specificity:
- ✅ Question 1: Good as-is
- ✏️ Question 2: "Should environment parameter support dev, staging, prod endpoints as defined in nf-graphql-services/config/environments.yml?"
- ✅ Question 3: Good as-is  
- ✏️ Question 4: "Should include all .graphqls files from nf-graphql-services/src/main/resources/schema/"
- ✅ Question 5: Good as-is
- ✏️ Question 6: "Use pattern: nf-graphql-sdk-{environment}-{version}.jar"

### Step 7: Tech Lead Analysis & Answers

**Tech Lead Agent provides detailed answers:**

**Q1 Answer:**
```
Yes, use the Maven build pattern from github-actions-templates/.github/workflows/maven-build.yml 
but modify for GraphQL code generation:

1. Add GraphQL Maven plugin configuration
2. Include code generation step before compilation
3. Use same caching strategy for dependencies
4. Reference pattern in lines 23-45 of maven-build.yml
```

**Q2 Answer:**
```
Use environment parameter with these endpoints:
- dev: https://dev-graphql.company.com/graphql  
- staging: https://staging-graphql.company.com/graphql
- prod: https://prod-graphql.company.com/graphql

Follow config pattern in nf-graphql-services/config/environments.yml lines 12-28.
Add validation to ensure only valid environments are accepted.
```

**Q3 Answer:**
```
Yes, follow java-sdk-commons structure:
- Generated classes: src/main/java/com/company/nf/graphql/client/
- Models: src/main/java/com/company/nf/graphql/model/  
- Utilities: src/main/java/com/company/nf/graphql/util/
- Tests: src/test/java/com/company/nf/graphql/

Use same package naming convention as java-sdk-commons/src/main/java/
```

(Additional detailed answers for Q4-Q6...)

### Step 8: Jira Card Generation

**Jira Card Agent creates comprehensive card:**

```markdown
# GitHub Action: Auto-Build NF-GraphQL Java SDK

## Summary
Create automated GitHub Action for building type-safe GraphQL client SDKs from NF-GraphQL services with environment-specific configuration.

## Description

### Implementation Plan
1. **Create GitHub Action Workflow**
   - File: `.github/workflows/build-graphql-sdk.yml`
   - Base on pattern from `github-actions-templates/.github/workflows/maven-build.yml`
   - Add GraphQL code generation step

2. **Configure GraphQL Code Generation**
   - Add GraphQL Maven plugin to `pom.xml`
   - Source schema: `nf-graphql-services/src/main/resources/schema/*.graphqls`
   - Output: `src/main/java/com/company/nf/graphql/`

3. **Environment Configuration**
   - Support dev, staging, prod environments
   - Endpoint configuration from `nf-graphql-services/config/environments.yml`
   - Manual trigger with environment parameter

4. **Artifact Publishing**
   - Package as JAR: `nf-graphql-sdk-{environment}-{version}.jar`
   - Publish to company Maven repository
   - Include source and documentation JARs

### Files to Create/Modify
- **NEW**: `.github/workflows/build-graphql-sdk.yml` (GitHub Action workflow)
- **MODIFY**: `pom.xml` (add GraphQL Maven plugin configuration)
- **NEW**: `src/main/resources/graphql-config.properties` (environment endpoints)
- **NEW**: `README-SDK.md` (SDK usage documentation)

### Database Changes
None required.

### Testing Strategy
- Unit tests for generated client classes
- Integration tests against dev environment
- Verify SDK artifacts are properly packaged
- Test manual trigger with different environments

### Acceptance Criteria
- [ ] GitHub Action can be triggered manually from nf-graphql-subgraph-template
- [ ] Action accepts environment parameter (dev/staging/prod)  
- [ ] Generated SDK includes type-safe GraphQL client classes
- [ ] Artifacts are published with correct naming convention
- [ ] Action fails gracefully with clear error messages
- [ ] Generated code follows company Java standards

## Technical Details

**Environment Endpoints:**
- dev: https://dev-graphql.company.com/graphql
- staging: https://staging-graphql.company.com/graphql  
- prod: https://prod-graphql.company.com/graphql

**Maven Dependencies:**
```xml
<dependency>
    <groupId>com.graphql-java-generator</groupId>
    <artifactId>graphql-maven-plugin</artifactId>
    <version>1.18</version>
</dependency>
```

**Package Structure:**
```
com.company.nf.graphql.client/
  ├── GraphQLClient.java
  ├── QueryExecutor.java  
  └── ResponseHandler.java
com.company.nf.graphql.model/
  ├── User.java
  ├── Order.java
  └── [Generated POJOs]
```

## Story Points: 8
## Labels: github-actions, java-sdk, graphql, infrastructure
## Epic: Developer Tooling Automation
```

### Step 9: Final Review & Creation

Developer reviews the card:
- ✅ Implementation plan is detailed and actionable
- ✅ File references are accurate  
- ✅ Technical details include exact configurations
- ✅ Acceptance criteria are measurable
- ✏️ Adds company-specific Jira labels

Clicks **"Create Jira Card"** → Card is created in Jira with ID `INFRA-456`

Task status updates to **"Completed"** with Jira card reference.

## Results

**Time Taken:** 4 minutes total
- Task selection: 30 seconds
- Repository selection: 1 minute  
- Question review: 1 minute
- Answer review: 1 minute
- Card review & creation: 30 seconds

**vs Traditional Approach (45+ minutes):**
- Research existing patterns: 15 minutes
- Understand GraphQL schema structure: 10 minutes
- Research GitHub Actions best practices: 10 minutes
- Write implementation plan: 10 minutes
- Create Jira card: 5 minutes

**Quality Improvement:**
- ✅ References actual code files and patterns
- ✅ Includes specific technical configurations  
- ✅ Follows company naming conventions
- ✅ Comprehensive acceptance criteria
- ✅ No missed implementation details

## What Makes This Powerful

1. **Context-Aware**: AI analyzed your actual repositories to understand existing patterns
2. **Specific**: Generated concrete file paths, configurations, and code patterns
3. **Consistent**: Followed existing company conventions automatically  
4. **Complete**: Nothing missed - from environment config to testing strategy
5. **Actionable**: Developer can start implementing immediately without additional research

This is the power of having AI agents that understand your entire codebase context rather than providing generic advice!