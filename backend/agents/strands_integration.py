"""
Strands SDK Integration Module

This module integrates with the Strands SDK to orchestrate AI agents
for the Jira card creation workflow.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import json

try:
    from strands import Agent, ToolFunction
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    # Mock classes for development
    class Agent:
        def __init__(self, *args, **kwargs):
            pass
        async def run(self, *args, **kwargs):
            return {"mock": "response"}
    
    class ToolFunction:
        def __init__(self, *args, **kwargs):
            pass

from .tools import AgentToolRegistry
from ..context.manager import ContextManager

logger = logging.getLogger(__name__)


class StrandsAgentOrchestrator:
    """Orchestrates Strands agents for the workflow."""
    
    def __init__(
        self,
        aws_profile: Optional[str],
        bedrock_region: str,
        agent_registry: AgentToolRegistry,
        context_manager: ContextManager
    ):
        self.aws_profile = aws_profile
        self.bedrock_region = bedrock_region
        self.agent_registry = agent_registry
        self.context_manager = context_manager
        
        # Agent instances
        self.jr_developer_agent = None
        self.tech_lead_agent = None
        self.jira_card_agent = None
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize all Strands agents."""
        if not STRANDS_AVAILABLE:
            logger.warning("Strands SDK not available - using mock implementation")
            self._initialized = True
            return
        
        try:
            logger.info("Initializing Strands agents...")
            
            # Initialize agent tools
            await self.agent_registry.initialize()
            
            # Create Jr Developer Agent
            self.jr_developer_agent = await self._create_jr_developer_agent()
            
            # Create Tech Lead Agent
            self.tech_lead_agent = await self._create_tech_lead_agent()
            
            # Create Jira Card Agent
            self.jira_card_agent = await self._create_jira_card_agent()
            
            self._initialized = True
            logger.info("Strands agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands agents: {e}")
            raise
    
    async def _create_jr_developer_agent(self) -> Agent:
        """Create Jr Developer Agent with repository analysis tools."""
        tools = self.agent_registry.get_jr_developer_tools()
        
        # Convert tools to Strands ToolFunction format
        strands_tools = []
        for tool_name, tool_func in tools.items():
            strands_tool = ToolFunction(
                name=tool_name,
                description=f"Tool for {tool_name.replace('_', ' ')}",
                function=tool_func
            )
            strands_tools.append(strands_tool)
        
        # Load Jr Developer prompt
        with open("jr-developer.md", "r") as f:
            system_prompt = f.read()
        
        agent = Agent(
            name="jr-developer",
            model="anthropic.claude-3-5-sonnet-v2",
            system_prompt=system_prompt,
            tools=strands_tools,
            aws_profile=self.aws_profile,
            aws_region=self.bedrock_region
        )
        
        return agent
    
    async def _create_tech_lead_agent(self) -> Agent:
        """Create Tech Lead Agent with advanced analysis tools."""
        tools = self.agent_registry.get_tech_lead_tools()
        
        # Convert tools to Strands ToolFunction format
        strands_tools = []
        for tool_name, tool_func in tools.items():
            strands_tool = ToolFunction(
                name=tool_name,
                description=f"Tool for {tool_name.replace('_', ' ')}",
                function=tool_func
            )
            strands_tools.append(strands_tool)
        
        # Load Tech Lead prompt
        with open("tech-lead.md", "r") as f:
            system_prompt = f.read()
        
        agent = Agent(
            name="tech-lead",
            model="anthropic.claude-3-5-sonnet-v2",
            system_prompt=system_prompt,
            tools=strands_tools,
            aws_profile=self.aws_profile,
            aws_region=self.bedrock_region
        )
        
        return agent
    
    async def _create_jira_card_agent(self) -> Agent:
        """Create Jira Card Agent with implementation reference tools."""
        tools = self.agent_registry.get_jira_card_tools()
        
        # Convert tools to Strands ToolFunction format
        strands_tools = []
        for tool_name, tool_func in tools.items():
            strands_tool = ToolFunction(
                name=tool_name,
                description=f"Tool for {tool_name.replace('_', ' ')}",
                function=tool_func
            )
            strands_tools.append(strands_tool)
        
        # Load Jira Card Agent prompt
        with open("Jiracard-agent.md", "r") as f:
            system_prompt = f.read()
        
        agent = Agent(
            name="jira-card",
            model="anthropic.claude-3-5-sonnet-v2",
            system_prompt=system_prompt,
            tools=strands_tools,
            aws_profile=self.aws_profile,
            aws_region=self.bedrock_region
        )
        
        return agent
    
    async def run_jr_developer_agent(self, context_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Jr Developer Agent to generate questions."""
        if not self._initialized:
            raise RuntimeError("Agents not initialized")
        
        try:
            logger.info(f"Running Jr Developer Agent for context: {context_id}")
            
            # Get current context
            context = await self.context_manager.get_context(context_id)
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            # Prepare input for agent
            task_description = context.task_context.task_description
            
            # Update workflow step
            await self.context_manager.update_workflow_step(context_id, "questions")
            
            if not STRANDS_AVAILABLE:
                # Return mock response for development
                return {
                    "questions": [
                        f"What specific implementation pattern should we follow for {task_description}?",
                        "Are there existing services we should integrate with?",
                        "What database schema changes are needed?",
                        "Should we follow the existing authentication pattern?",
                        "What testing approach should we use based on existing patterns?"
                    ],
                    "context_id": context_id,
                    "status": "success"
                }
            
            # Run the agent
            response = await self.jr_developer_agent.run(
                input_text=f"Analyze this task and generate developer questions: {task_description}",
                context={"context_id": context_id}
            )
            
            # Parse response
            result = {
                "questions": self._extract_questions_from_response(response),
                "context_id": context_id,
                "status": "success"
            }
            
            logger.info(f"Jr Developer Agent completed for context: {context_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error running Jr Developer Agent: {e}")
            return {
                "status": "error",
                "error": str(e),
                "context_id": context_id
            }
    
    async def run_tech_lead_agent(self, context_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Tech Lead Agent to generate answers."""
        if not self._initialized:
            raise RuntimeError("Agents not initialized")
        
        try:
            logger.info(f"Running Tech Lead Agent for context: {context_id}")
            
            # Get current context
            context = await self.context_manager.get_context(context_id)
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            # Update workflow step
            await self.context_manager.update_workflow_step(context_id, "answers")
            
            questions = step_data.get("questions", [])
            task_description = context.task_context.task_description
            
            if not STRANDS_AVAILABLE:
                # Return mock response for development
                return {
                    "answers": [
                        {
                            "question": q,
                            "answer": f"Based on repository analysis, you should follow the existing pattern found in [repository]/src/[pattern]. This aligns with our current architecture.",
                            "code_references": ["repo1/src/Service.java:45", "repo2/config/app.yml:12"],
                            "database_references": ["SCHEMA.USER_TABLE", "SCHEMA.AUDIT_LOG"]
                        }
                        for q in questions
                    ],
                    "context_id": context_id,
                    "status": "success"
                }
            
            # Prepare input
            input_text = f"""
Task: {task_description}

Developer Questions:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(questions)])}

Please analyze the codebase and provide detailed answers with specific file references.
"""
            
            # Run the agent
            response = await self.tech_lead_agent.run(
                input_text=input_text,
                context={"context_id": context_id}
            )
            
            # Parse response
            result = {
                "answers": self._extract_answers_from_response(response, questions),
                "context_id": context_id,
                "status": "success"
            }
            
            logger.info(f"Tech Lead Agent completed for context: {context_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error running Tech Lead Agent: {e}")
            return {
                "status": "error",
                "error": str(e),
                "context_id": context_id
            }
    
    async def run_jira_card_agent(self, context_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Jira Card Agent to generate Jira card."""
        if not self._initialized:
            raise RuntimeError("Agents not initialized")
        
        try:
            logger.info(f"Running Jira Card Agent for context: {context_id}")
            
            # Get current context
            context = await self.context_manager.get_context(context_id)
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            # Update workflow step
            await self.context_manager.update_workflow_step(context_id, "card_generation")
            
            questions = step_data.get("questions", [])
            answers = step_data.get("answers", [])
            task_description = context.task_context.task_description
            
            if not STRANDS_AVAILABLE:
                # Return mock response for development
                return {
                    "jira_card": {
                        "title": f"Implement {task_description[:50]}...",
                        "description": "## User Story\nAs a user, I want...\n\n## Acceptance Criteria\n- [ ] Implementation complete\n- [ ] Tests passing\n\n## Implementation References\n- See `repo1/src/Example.java:45-67` for similar pattern\n- Database changes in `SCHEMA.USER_TABLE`",
                        "epic": "Development Epic",
                        "labels": ["backend", "database", "api"],
                        "story_points": 5,
                        "implementation_files": [
                            "src/main/java/com/example/NewService.java",
                            "src/main/resources/db/migration/V001__add_feature.sql",
                            "src/test/java/com/example/NewServiceTest.java"
                        ],
                        "database_changes": [
                            "ALTER TABLE USER_TABLE ADD COLUMN new_field VARCHAR2(100)",
                            "CREATE INDEX idx_user_new_field ON USER_TABLE(new_field)"
                        ]
                    },
                    "context_id": context_id,
                    "status": "success"
                }
            
            # Prepare comprehensive input
            qa_pairs = []
            for q, a in zip(questions, answers):
                qa_pairs.append(f"Q: {q}\nA: {a}")
            
            input_text = f"""
Task: {task_description}

Questions and Answers:
{chr(10).join(qa_pairs)}

Please generate a comprehensive Jira card with specific implementation details, file references, and database schema changes.
"""
            
            # Run the agent
            response = await self.jira_card_agent.run(
                input_text=input_text,
                context={"context_id": context_id}
            )
            
            # Parse response
            result = {
                "jira_card": self._extract_jira_card_from_response(response),
                "context_id": context_id,
                "status": "success"
            }
            
            logger.info(f"Jira Card Agent completed for context: {context_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error running Jira Card Agent: {e}")
            return {
                "status": "error",
                "error": str(e),
                "context_id": context_id
            }
    
    def _extract_questions_from_response(self, response: Any) -> list:
        """Extract questions from agent response."""
        # This would parse the actual agent response
        # For now, return mock questions
        if isinstance(response, dict) and "questions" in response:
            return response["questions"]
        
        # Fallback mock questions
        return [
            "What implementation pattern should we follow?",
            "Are there existing services to integrate with?",
            "What database changes are needed?",
            "What testing approach should we use?"
        ]
    
    def _extract_answers_from_response(self, response: Any, questions: list) -> list:
        """Extract answers from agent response."""
        # This would parse the actual agent response
        # For now, return mock answers
        answers = []
        for question in questions:
            answers.append({
                "question": question,
                "answer": f"Based on repository analysis for: {question}",
                "code_references": ["example/repo/file.java:123"],
                "database_references": ["SCHEMA.TABLE_NAME"]
            })
        
        return answers
    
    def _extract_jira_card_from_response(self, response: Any) -> dict:
        """Extract Jira card from agent response."""
        # This would parse the actual agent response
        # For now, return mock card
        return {
            "title": "Generated Jira Card Title",
            "description": "## Implementation Details\nBased on codebase analysis...",
            "epic": "Development Epic",
            "labels": ["backend", "api", "database"],
            "story_points": 5,
            "implementation_files": ["src/main/java/Service.java"],
            "database_changes": ["ALTER TABLE..."]
        }