# Multi-Agent Jira Card Creator - Installation Guide

## Overview
This application automates Jira card creation using AI agents that analyze your local repositories and database schemas. It provides a 6x speed improvement over traditional development workflows.

## System Requirements

### Hardware
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 5GB free space for Docker images and application data
- **Network**: Stable internet connection for AWS Bedrock API calls

### Software Prerequisites
- **Docker**: Version 20.10+ with Docker Compose
- **Git**: For repository access
- **Windows**: Windows 10/11 with WSL2 OR Windows Server 2019+
- **OR Linux**: Ubuntu 18.04+, CentOS 7+, or equivalent
- **OR macOS**: macOS 10.15+

## Pre-Installation Setup

### 1. AWS Account & Credentials
You need an AWS account with Bedrock access:

1. **Create AWS Account** (if you don't have one)
   - Go to https://aws.amazon.com/
   - Sign up for an account

2. **Enable Bedrock Access**
   - Go to AWS Bedrock console
   - Request access to **Claude 3.7 Sonnet** model
   - Wait for approval (usually 24-48 hours)

3. **Create IAM User for Application**
   ```bash
   # Required permissions for the IAM user:
   - bedrock:InvokeModel
   - bedrock:InvokeModelWithResponseStream
   - bedrock:ListFoundationModels
   ```

4. **Get AWS Credentials**
   - Access Key ID
   - Secret Access Key
   - AWS Region (where Bedrock is available, e.g., us-east-1)

### 2. Jira Setup
1. **Create API Token**
   - Go to Jira → Profile → Manage Account → Security
   - Create API Token
   - Save the token securely

2. **Note Your Jira Details**
   - Jira Base URL (e.g., https://yourcompany.atlassian.net)
   - Your email address
   - Project Key where cards will be created

### 3. Repository Setup
1. **Prepare Local Repositories**
   - Ensure all repositories are checked out locally
   - Place them in a single parent directory (e.g., `/home/user/repositories/`)
   - Make sure they're accessible and have proper permissions

2. **Database Access (Optional)**
   - If using Oracle database analysis
   - Ensure database is accessible from the application server
   - Have read-only credentials ready

## Installation Steps

### Step 1: Download Application
```bash
# Clone the repository
git clone <repository-url>
cd bl-docs-

# Verify all files are present
ls -la
# You should see: backend/, frontend/, docker-compose.yml, etc.
```

### Step 2: Configure Environment
```bash
# Copy the environment template
cp .env.template .env

# Edit the configuration
nano .env
```

**Complete the .env file with your details:**
```bash
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Jira Configuration
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY

# Repository Configuration
REPOSITORIES_PATH=/path/to/your/repositories
# Example: /home/user/repositories or C:\Users\user\repositories

# Database Configuration (Optional)
DATABASE_ENABLED=false
DATABASE_JDBC_URL=jdbc:oracle:thin:@localhost:1521:xe
DATABASE_USERNAME=your_db_user
DATABASE_PASSWORD=your_db_password

# Application Configuration
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=4200
LOG_LEVEL=INFO
```

### Step 3: Update Docker Compose
Edit `docker-compose.yml` to match your local paths:

```yaml
volumes:
  # Update this path to match your REPOSITORIES_PATH
  - "C:/Users/yourname/repositories:/app/repositories:ro"
  # OR for Linux/macOS:
  # - "/home/user/repositories:/app/repositories:ro"
```

### Step 4: Start the Application
```bash
# Build and start all services
docker-compose up -d --build

# Check that services are running
docker-compose ps

# You should see:
# - jira-backend (running)
# - jira-frontend (running)
```

### Step 5: Verify Installation
1. **Check Backend Health**
   ```bash
   curl http://localhost:8000/api/health
   # Should return: {"status": "healthy", "timestamp": "..."}
   ```

2. **Access Frontend**
   - Open browser to http://localhost:4200
   - You should see the dashboard

3. **Test Repository Scanning**
   - Click "Scan Repositories" on the dashboard
   - Should show your local repositories

## First Run Configuration

### 1. Initial System Check
1. Go to http://localhost:4200
2. Check System Status card - all should be green:
   - ✅ API Health: healthy
   - ✅ Repository Scanner: Active
   - ✅ Database: Connected (if enabled)
   - ✅ AI Agents: Ready

### 2. Repository Verification
1. Click "Scan Repositories"
2. Verify your repositories appear in the table
3. Check that languages and frameworks are detected correctly

### 3. Create First Task
1. Fill out the task creation form:
   - **Task ID**: TEST-001
   - **Task Type**: Feature
   - **Description**: Test task to verify system works
2. Click "Create Task & Start Workflow"
3. Follow the workflow through all steps

## Troubleshooting

### Common Issues

**1. "Container failed to start"**
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Common fixes:
# - Verify .env file is complete
# - Check file permissions on repositories path
# - Ensure Docker has enough memory allocated
```

**2. "Repository scanner not working"**
```bash
# Verify repository path
docker-compose exec backend ls -la /app/repositories

# Should show your repository directories
# If empty, check volume mount in docker-compose.yml
```

**3. "AWS Bedrock connection failed"**
```bash
# Check AWS credentials
docker-compose exec backend python -c "
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
print('AWS connection successful')
"

# Common fixes:
# - Verify AWS credentials in .env
# - Ensure Bedrock access is approved
# - Check AWS region is correct
```

**4. "Jira integration not working"**
```bash
# Test Jira connection
curl -u "your-email:your-api-token" \
  "https://yourcompany.atlassian.net/rest/api/2/myself"

# Should return your user info
# If fails, verify JIRA_* variables in .env
```

**5. "Frontend not loading"**
```bash
# Check frontend logs
docker-compose logs frontend

# Verify frontend is accessible
curl http://localhost:4200

# Common fixes:
# - Restart frontend container
# - Check port conflicts (4200 in use?)
```

### Performance Optimization

**For Large Repository Sets (50+)**
```bash
# Increase memory for backend container
# Edit docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

**For Faster Repository Scanning**
```bash
# Add to .env:
REPO_SCAN_PARALLEL_LIMIT=10
REPO_SCAN_CACHE_ENABLED=true
```

## Security Considerations

### Production Deployment
1. **Change Default Ports**
   - Use reverse proxy (nginx/apache)
   - Enable HTTPS

2. **Secure Environment Variables**
   - Use Docker secrets or external secret management
   - Rotate API tokens regularly

3. **Network Security**
   - Run behind firewall
   - Limit access to authorized users only

### Data Privacy
- All repository analysis happens locally
- No code is sent to external services except AI model inference
- Database connections use read-only access
- Audit logs available in application logs

## Backup and Maintenance

### Regular Maintenance
```bash
# Weekly cleanup
docker system prune -f

# Update application (when new version available)
git pull
docker-compose down
docker-compose up -d --build
```

### Backup Important Data
```bash
# Backup configuration
cp .env .env.backup

# Backup application logs
docker-compose logs > application.log

# Note: No persistent data is stored by the application
# All analysis is performed fresh each run
```

## Getting Help

### Log Files
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Performance Monitoring
- Backend health: http://localhost:8000/api/health
- Detailed system info available on dashboard "System Information" tab

### Support Information
- Include .env file (with sensitive data redacted)
- Include output of `docker-compose ps`
- Include relevant log excerpts
- Describe the specific error and steps to reproduce

## Success Criteria
Your installation is successful when:
- ✅ Dashboard loads at http://localhost:4200
- ✅ System status shows all green indicators
- ✅ Repository scan finds your local repositories
- ✅ You can create a test task and complete the workflow
- ✅ Jira card is created successfully

**Expected Performance**: Complete workflow should take 3-5 minutes compared to 30+ minutes with traditional methods.

---

*This installation guide is designed to be followed by any technical user without prior knowledge of the system. If you encounter issues not covered here, all components include comprehensive error messages and logging.*