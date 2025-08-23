"""
Agent Tools Module

This module provides enhanced tools for Strands agents to analyze repositories and databases.
These tools enable agents to perform code analysis, database schema exploration, and 
context-aware question/answer generation.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any, Union
from dataclasses import asdict
import asyncio
from pathlib import Path

from ..repository.scanner import RepositoryScanner, RepositoryInfo
from ..database.connector import DatabaseConnector, SchemaAnalysis, TableInfo, QueryResult

logger = logging.getLogger(__name__)


class RepositoryTools:
    """Tools for repository analysis and code exploration."""
    
    def __init__(self, repository_scanner: RepositoryScanner):
        self.scanner = repository_scanner
    
    async def scan_repositories(self, force_refresh: bool = False) -> str:
        """
        Scan all repositories in the configured path.
        
        Args:
            force_refresh: Whether to force a fresh scan ignoring cache
            
        Returns:
            JSON string containing repository information
        """
        try:
            repositories = await self.scanner.scan_repositories(force_refresh)
            
            # Convert to JSON-serializable format
            repo_data = []
            for repo in repositories:
                repo_dict = asdict(repo)
                # Convert datetime objects to strings
                repo_dict['last_scanned'] = repo_dict['last_scanned'].isoformat()
                if repo_dict.get('git_info') and repo_dict['git_info'].get('last_commit_date'):
                    repo_dict['git_info']['last_commit_date'] = repo_dict['git_info']['last_commit_date'].isoformat()
                repo_data.append(repo_dict)
            
            result = {
                "status": "success",
                "repository_count": len(repositories),
                "repositories": repo_data
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error scanning repositories: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def get_repository_list(self) -> str:
        """
        Get a list of available repositories with basic information.
        
        Returns:
            JSON string containing repository list
        """
        try:
            repos = []
            for repo_info in self.scanner._cache.values():
                repos.append({
                    "name": repo_info.name,
                    "path": repo_info.path,
                    "primary_language": repo_info.primary_language,
                    "languages": repo_info.languages,
                    "frameworks": repo_info.frameworks,
                    "file_count": repo_info.file_count,
                    "size_mb": round(repo_info.size_bytes / (1024 * 1024), 2)
                })
            
            return json.dumps({
                "status": "success",
                "repositories": sorted(repos, key=lambda x: x["name"])
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting repository list: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def get_repository_details(self, repo_name: str) -> str:
        """
        Get detailed information about a specific repository.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            JSON string containing detailed repository information
        """
        try:
            repo_info = self.scanner.get_repository_by_name(repo_name)
            if not repo_info:
                return json.dumps({
                    "status": "error",
                    "error": f"Repository '{repo_name}' not found"
                })
            
            repo_dict = asdict(repo_info)
            # Convert datetime objects to strings
            repo_dict['last_scanned'] = repo_dict['last_scanned'].isoformat()
            if repo_dict.get('git_info') and repo_dict['git_info'].get('last_commit_date'):
                repo_dict['git_info']['last_commit_date'] = repo_dict['git_info']['last_commit_date'].isoformat()
            
            return json.dumps({
                "status": "success",
                "repository": repo_dict
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting repository details for {repo_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def read_file(self, repo_name: str, file_path: str) -> str:
        """
        Read the content of a specific file in a repository.
        
        Args:
            repo_name: Name of the repository
            file_path: Relative path to the file within the repository
            
        Returns:
            JSON string containing file content
        """
        try:
            content = self.scanner.get_file_content(repo_name, file_path)
            if content is None:
                return json.dumps({
                    "status": "error",
                    "error": f"File '{file_path}' not found in repository '{repo_name}'"
                })
            
            return json.dumps({
                "status": "success",
                "file_path": file_path,
                "repository": repo_name,
                "content": content,
                "line_count": len(content.split('\n')),
                "character_count": len(content)
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error reading file {file_path} from {repo_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def search_code_patterns(self, pattern: str, repo_names: Optional[List[str]] = None, max_results: int = 50) -> str:
        """
        Search for code patterns across repositories.
        
        Args:
            pattern: Pattern to search for
            repo_names: List of repository names to search in (optional)
            max_results: Maximum number of results to return
            
        Returns:
            JSON string containing search results
        """
        try:
            results = self.scanner.search_code_patterns(pattern, repo_names)
            
            # Limit results
            limited_results = results[:max_results]
            
            return json.dumps({
                "status": "success",
                "pattern": pattern,
                "total_matches": len(results),
                "returned_matches": len(limited_results),
                "repositories_searched": repo_names or "all",
                "matches": limited_results
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error searching for pattern '{pattern}': {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def analyze_dependencies(self, repo_name: str) -> str:
        """
        Get dependency analysis for a specific repository.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            JSON string containing dependency information
        """
        try:
            repo_info = self.scanner.get_repository_by_name(repo_name)
            if not repo_info:
                return json.dumps({
                    "status": "error",
                    "error": f"Repository '{repo_name}' not found"
                })
            
            # Group dependencies by type
            deps_by_type = {}
            for dep in repo_info.dependencies:
                if dep.type not in deps_by_type:
                    deps_by_type[dep.type] = []
                deps_by_type[dep.type].append(asdict(dep))
            
            return json.dumps({
                "status": "success",
                "repository": repo_name,
                "total_dependencies": len(repo_info.dependencies),
                "dependencies_by_type": deps_by_type
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies for {repo_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def get_file_structure(self, repo_name: str, max_depth: int = 3) -> str:
        """
        Get the file structure of a repository.
        
        Args:
            repo_name: Name of the repository
            max_depth: Maximum depth of directory structure to return
            
        Returns:
            JSON string containing file structure
        """
        try:
            repo_info = self.scanner.get_repository_by_name(repo_name)
            if not repo_info:
                return json.dumps({
                    "status": "error",
                    "error": f"Repository '{repo_name}' not found"
                })
            
            # Flatten structure to specified depth
            def flatten_structure(structure, current_depth=0):
                if current_depth >= max_depth:
                    return "..."
                
                result = {}
                for name, item in structure.items():
                    if item.get('type') == 'directory':
                        result[name] = flatten_structure(item.get('children', {}), current_depth + 1)
                    else:
                        result[name] = {
                            'type': 'file',
                            'language': item.get('language'),
                            'size': item.get('size')
                        }
                return result
            
            flattened = flatten_structure(repo_info.file_structure)
            
            return json.dumps({
                "status": "success",
                "repository": repo_name,
                "max_depth": max_depth,
                "file_structure": flattened
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting file structure for {repo_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })


class DatabaseTools:
    """Tools for database analysis and schema exploration."""
    
    def __init__(self, database_connector: DatabaseConnector):
        self.connector = database_connector
    
    async def test_connection(self) -> str:
        """
        Test the database connection.
        
        Returns:
            JSON string containing connection status
        """
        try:
            is_connected = await self.connector.test_connection()
            
            return json.dumps({
                "status": "success",
                "connected": is_connected,
                "message": "Connection successful" if is_connected else "Connection failed"
            })
            
        except Exception as e:
            logger.error(f"Error testing database connection: {e}")
            return json.dumps({
                "status": "error",
                "connected": False,
                "error": str(e)
            })
    
    async def analyze_schema(self, schema_name: str, force_refresh: bool = False) -> str:
        """
        Analyze a database schema.
        
        Args:
            schema_name: Name of the schema to analyze
            force_refresh: Whether to force a fresh analysis
            
        Returns:
            JSON string containing schema analysis
        """
        try:
            schema_analysis = await self.connector.analyze_schema(schema_name, force_refresh)
            
            # Convert to JSON-serializable format
            analysis_dict = asdict(schema_analysis)
            analysis_dict['analysis_date'] = analysis_dict['analysis_date'].isoformat()
            
            # Convert table info
            for table in analysis_dict['tables']:
                table['last_analyzed'] = table['last_analyzed'].isoformat()
            
            return json.dumps({
                "status": "success",
                "schema_analysis": analysis_dict
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing schema {schema_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    async def get_table_info(self, schema_name: str, table_name: str) -> str:
        """
        Get detailed information about a specific table.
        
        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            
        Returns:
            JSON string containing table information
        """
        try:
            table_info = await self.connector.get_table_info(schema_name, table_name)
            if not table_info:
                return json.dumps({
                    "status": "error",
                    "error": f"Table '{table_name}' not found in schema '{schema_name}'"
                })
            
            # Convert to JSON-serializable format
            table_dict = asdict(table_info)
            table_dict['last_analyzed'] = table_dict['last_analyzed'].isoformat()
            
            return json.dumps({
                "status": "success",
                "table_info": table_dict
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting table info for {schema_name}.{table_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    async def search_tables(self, schema_name: str, pattern: str) -> str:
        """
        Search for tables matching a pattern.
        
        Args:
            schema_name: Name of the schema
            pattern: Pattern to search for
            
        Returns:
            JSON string containing matching table names
        """
        try:
            table_names = await self.connector.search_tables(schema_name, pattern)
            
            return json.dumps({
                "status": "success",
                "schema": schema_name,
                "pattern": pattern,
                "matches": table_names,
                "match_count": len(table_names)
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error searching tables in {schema_name} with pattern {pattern}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a read-only query against the database.
        
        Args:
            query: SQL query to execute
            parameters: Optional query parameters
            
        Returns:
            JSON string containing query results
        """
        try:
            result = await self.connector.execute_query(query, parameters)
            
            # Convert result to JSON-serializable format
            result_dict = asdict(result)
            
            return json.dumps({
                "status": "success",
                "query_result": result_dict
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    async def get_table_relationships(self, schema_name: str, table_name: str) -> str:
        """
        Get relationship information for a table.
        
        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            
        Returns:
            JSON string containing relationship information
        """
        try:
            relationships = await self.connector.get_table_relationships(schema_name, table_name)
            
            return json.dumps({
                "status": "success",
                "table": f"{schema_name}.{table_name}",
                "relationships": relationships
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting relationships for {schema_name}.{table_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    async def get_table_sample(self, schema_name: str, table_name: str, limit: int = 10) -> str:
        """
        Get a sample of data from a table.
        
        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            JSON string containing sample data
        """
        try:
            result = await self.connector.query_executor.get_table_sample(schema_name, table_name, limit)
            
            # Convert result to JSON-serializable format
            result_dict = asdict(result)
            
            return json.dumps({
                "status": "success",
                "table": f"{schema_name}.{table_name}",
                "sample_data": result_dict
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting sample data for {schema_name}.{table_name}: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })


class ContextTools:
    """Tools for managing repository and database context."""
    
    def __init__(self, repository_tools: RepositoryTools, database_tools: DatabaseTools):
        self.repo_tools = repository_tools
        self.db_tools = database_tools
        self._context = {
            "selected_repositories": [],
            "selected_schema": None,
            "task_context": {}
        }
    
    def set_repository_context(self, repository_names: List[str]) -> str:
        """
        Set the repository context for analysis.
        
        Args:
            repository_names: List of repository names to include in context
            
        Returns:
            JSON string confirming context update
        """
        try:
            # Validate repositories exist
            available_repos = [repo['name'] for repo in json.loads(self.repo_tools.get_repository_list())['repositories']]
            
            invalid_repos = [name for name in repository_names if name not in available_repos]
            if invalid_repos:
                return json.dumps({
                    "status": "error",
                    "error": f"Invalid repositories: {invalid_repos}",
                    "available_repositories": available_repos
                })
            
            self._context["selected_repositories"] = repository_names
            
            return json.dumps({
                "status": "success",
                "message": f"Repository context set to {len(repository_names)} repositories",
                "selected_repositories": repository_names
            })
            
        except Exception as e:
            logger.error(f"Error setting repository context: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def set_database_context(self, schema_name: str) -> str:
        """
        Set the database schema context for analysis.
        
        Args:
            schema_name: Name of the schema to use for context
            
        Returns:
            JSON string confirming context update
        """
        try:
            self._context["selected_schema"] = schema_name
            
            return json.dumps({
                "status": "success",
                "message": f"Database context set to schema '{schema_name}'",
                "selected_schema": schema_name
            })
            
        except Exception as e:
            logger.error(f"Error setting database context: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def get_current_context(self) -> str:
        """
        Get the current analysis context.
        
        Returns:
            JSON string containing current context
        """
        return json.dumps({
            "status": "success",
            "context": self._context
        }, indent=2)
    
    def set_task_context(self, task_info: Dict[str, Any]) -> str:
        """
        Set additional task-specific context information.
        
        Args:
            task_info: Dictionary containing task-specific context
            
        Returns:
            JSON string confirming context update
        """
        try:
            self._context["task_context"] = task_info
            
            return json.dumps({
                "status": "success",
                "message": "Task context updated",
                "task_context": task_info
            })
            
        except Exception as e:
            logger.error(f"Error setting task context: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    async def analyze_context_relevance(self, task_description: str) -> str:
        """
        Analyze which repositories and database elements are relevant to a task.
        
        Args:
            task_description: Description of the task to analyze
            
        Returns:
            JSON string containing relevance analysis
        """
        try:
            # Simple keyword-based relevance analysis
            keywords = task_description.lower().split()
            
            # Analyze repository relevance
            repo_relevance = []
            if self._context["selected_repositories"]:
                for repo_name in self._context["selected_repositories"]:
                    repo_details = json.loads(self.repo_tools.get_repository_details(repo_name))
                    if repo_details["status"] == "success":
                        repo_info = repo_details["repository"]
                        
                        # Calculate relevance score
                        score = 0
                        if any(keyword in repo_info["name"].lower() for keyword in keywords):
                            score += 3
                        if any(keyword in lang.lower() for lang in repo_info["languages"] for keyword in keywords):
                            score += 2
                        if any(keyword in fw.lower() for fw in repo_info["frameworks"] for keyword in keywords):
                            score += 2
                        
                        repo_relevance.append({
                            "repository": repo_name,
                            "relevance_score": score,
                            "reasons": []
                        })
            
            # Sort by relevance
            repo_relevance.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return json.dumps({
                "status": "success",
                "task_description": task_description,
                "repository_relevance": repo_relevance,
                "database_schema": self._context.get("selected_schema"),
                "recommendations": {
                    "most_relevant_repos": [r["repository"] for r in repo_relevance[:3]],
                    "use_database": bool(self._context.get("selected_schema"))
                }
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing context relevance: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })


class AgentToolRegistry:
    """Registry for all agent tools."""
    
    def __init__(self, repository_base_path: str, database_config: Optional[Dict[str, str]] = None):
        # Initialize repository scanner
        self.repository_scanner = RepositoryScanner(repository_base_path)
        self.repository_tools = RepositoryTools(self.repository_scanner)
        
        # Initialize database connector if config provided
        self.database_connector = None
        self.database_tools = None
        if database_config:
            self.database_connector = DatabaseConnector(
                jdbc_url=database_config["jdbc_url"],
                username=database_config["username"],
                password=database_config["password"]
            )
            self.database_tools = DatabaseTools(self.database_connector)
        
        # Initialize context tools
        self.context_tools = ContextTools(self.repository_tools, self.database_tools)
    
    def get_jr_developer_tools(self) -> Dict[str, Any]:
        """Get tools for Jr Developer agent."""
        tools = {
            # Repository analysis tools
            "scan_repositories": self.repository_tools.scan_repositories,
            "get_repository_list": self.repository_tools.get_repository_list,
            "get_repository_details": self.repository_tools.get_repository_details,
            "read_file": self.repository_tools.read_file,
            "search_code_patterns": self.repository_tools.search_code_patterns,
            "analyze_dependencies": self.repository_tools.analyze_dependencies,
            "get_file_structure": self.repository_tools.get_file_structure,
            
            # Context management
            "set_repository_context": self.context_tools.set_repository_context,
            "get_current_context": self.context_tools.get_current_context,
            "analyze_context_relevance": self.context_tools.analyze_context_relevance,
        }
        
        # Add database tools if available
        if self.database_tools:
            tools.update({
                "test_database_connection": self.database_tools.test_connection,
                "search_tables": self.database_tools.search_tables,
                "set_database_context": self.context_tools.set_database_context,
            })
        
        return tools
    
    def get_tech_lead_tools(self) -> Dict[str, Any]:
        """Get tools for Tech Lead agent."""
        # Tech Lead gets all Jr Developer tools plus advanced analysis
        tools = self.get_jr_developer_tools()
        
        # Add advanced database tools if available
        if self.database_tools:
            tools.update({
                "analyze_schema": self.database_tools.analyze_schema,
                "get_table_info": self.database_tools.get_table_info,
                "execute_query": self.database_tools.execute_query,
                "get_table_relationships": self.database_tools.get_table_relationships,
                "get_table_sample": self.database_tools.get_table_sample,
            })
        
        return tools
    
    def get_jira_card_tools(self) -> Dict[str, Any]:
        """Get tools for Jira Card agent."""
        # Jira Card agent gets subset of tools focused on reference generation
        tools = {
            # Repository reference tools
            "get_repository_list": self.repository_tools.get_repository_list,
            "get_repository_details": self.repository_tools.get_repository_details,
            "read_file": self.repository_tools.read_file,
            "search_code_patterns": self.repository_tools.search_code_patterns,
            "get_file_structure": self.repository_tools.get_file_structure,
            
            # Context tools
            "get_current_context": self.context_tools.get_current_context,
        }
        
        # Add database reference tools if available
        if self.database_tools:
            tools.update({
                "get_table_info": self.database_tools.get_table_info,
                "search_tables": self.database_tools.search_tables,
                "get_table_relationships": self.database_tools.get_table_relationships,
            })
        
        return tools
    
    async def initialize(self):
        """Initialize all tools and connections."""
        try:
            # Initialize repository scanner
            logger.info("Initializing repository scanner...")
            await self.repository_scanner.scan_repositories()
            
            # Initialize database connection if configured
            if self.database_connector:
                logger.info("Initializing database connection...")
                await self.database_connector.initialize()
            
            logger.info("Agent tools initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agent tools: {e}")
            raise
    
    def cleanup(self):
        """Cleanup resources."""
        if self.database_connector:
            self.database_connector.close()


# Example tool configurations for Strands agents
def get_strands_tool_configs():
    """Get tool configurations for Strands agents."""
    return {
        "jr_developer_tools": [
            {
                "name": "scan_repositories",
                "description": "Scan all repositories to get an overview of available codebases",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "force_refresh": {
                            "type": "boolean",
                            "description": "Force a fresh scan ignoring cache"
                        }
                    }
                }
            },
            {
                "name": "search_code_patterns",
                "description": "Search for specific patterns in code across repositories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "The pattern to search for"
                        },
                        "repo_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of repository names to search in"
                        }
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the content of a specific file in a repository",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_name": {
                            "type": "string",
                            "description": "Name of the repository"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file within the repository"
                        }
                    },
                    "required": ["repo_name", "file_path"]
                }
            }
        ]
    }