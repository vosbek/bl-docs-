"""
Repository Scanner Module

This module provides comprehensive scanning and analysis capabilities for local repositories.
It discovers, indexes, and analyzes 50+ local repositories to provide context for AI agents.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a specific file in a repository."""
    path: str
    size: int
    modified: datetime
    language: Optional[str]
    is_config: bool
    is_test: bool


@dataclass
class DependencyInfo:
    """Information about project dependencies."""
    name: str
    version: Optional[str]
    scope: str  # 'compile', 'test', 'runtime', etc.
    type: str   # 'maven', 'npm', 'pip', etc.


@dataclass
class GitInfo:
    """Git repository information."""
    branch: str
    last_commit: str
    last_commit_date: datetime
    remote_url: Optional[str]
    is_dirty: bool


@dataclass
class RepositoryInfo:
    """Complete information about a repository."""
    name: str
    path: str
    primary_language: str
    languages: List[str]
    frameworks: List[str]
    dependencies: List[DependencyInfo]
    file_structure: Dict[str, Any]
    git_info: Optional[GitInfo]
    size_bytes: int
    file_count: int
    last_scanned: datetime
    scan_duration: float


class LanguageDetector:
    """Detects programming languages based on file extensions and content."""
    
    LANGUAGE_EXTENSIONS = {
        'java': ['.java'],
        'python': ['.py'],
        'javascript': ['.js', '.jsx', '.ts', '.tsx'],
        'typescript': ['.ts', '.tsx'],
        'csharp': ['.cs'],
        'cpp': ['.cpp', '.cc', '.cxx', '.c++'],
        'c': ['.c', '.h'],
        'go': ['.go'],
        'rust': ['.rs'],
        'php': ['.php'],
        'ruby': ['.rb'],
        'swift': ['.swift'],
        'kotlin': ['.kt', '.kts'],
        'scala': ['.scala'],
        'groovy': ['.groovy'],
        'shell': ['.sh', '.bash', '.zsh'],
        'sql': ['.sql'],
        'xml': ['.xml'],
        'json': ['.json'],
        'yaml': ['.yml', '.yaml'],
        'properties': ['.properties'],
        'dockerfile': ['Dockerfile', 'dockerfile'],
    }
    
    CONFIG_FILES = {
        'pom.xml': 'maven',
        'build.gradle': 'gradle',
        'package.json': 'npm',
        'requirements.txt': 'pip',
        'Pipfile': 'pipenv',
        'composer.json': 'composer',
        'Cargo.toml': 'cargo',
        'go.mod': 'go-modules',
        'setup.py': 'python-setup',
        '.env': 'environment',
        'docker-compose.yml': 'docker-compose',
        'Dockerfile': 'docker',
    }
    
    FRAMEWORK_INDICATORS = {
        'spring': ['@SpringBootApplication', '@RestController', 'org.springframework'],
        'react': ['import React', 'from "react"', '"react"'],
        'angular': ['@angular/', '@Component', '@Injectable'],
        'vue': ['Vue.js', 'vue-router', 'vuex'],
        'django': ['from django', 'Django', 'django.'],
        'flask': ['from flask', 'Flask(', 'flask.'],
        'express': ['express()', 'require("express")', 'app.listen'],
        'nestjs': ['@nestjs/', '@Controller', '@Injectable'],
        'fastapi': ['from fastapi', 'FastAPI()', 'fastapi.'],
        'hibernate': ['@Entity', '@Table', 'hibernate.'],
        'jpa': ['@Repository', '@Entity', 'javax.persistence'],
        'mybatis': ['@Mapper', 'mybatis.'],
    }
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect the programming language of a file."""
        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path)
        
        # Check exact filename matches first (like Dockerfile)
        for lang, exts in self.LANGUAGE_EXTENSIONS.items():
            if file_name in exts or ext.lower() in exts:
                return lang
        
        return None
    
    def detect_frameworks(self, repo_path: str, file_infos: List[FileInfo]) -> List[str]:
        """Detect frameworks used in the repository."""
        frameworks = set()
        
        # Check dependency files
        for file_info in file_infos:
            file_name = os.path.basename(file_info.path)
            if file_name in self.CONFIG_FILES:
                frameworks.update(self._analyze_config_file(file_info.path))
        
        # Check source code for framework indicators
        source_files = [f for f in file_infos if f.language in ['java', 'javascript', 'typescript', 'python']]
        for file_info in source_files[:20]:  # Sample first 20 files for performance
            try:
                frameworks.update(self._analyze_source_file(file_info.path))
            except Exception as e:
                logger.warning(f"Error analyzing {file_info.path}: {e}")
        
        return list(frameworks)
    
    def _analyze_config_file(self, file_path: str) -> Set[str]:
        """Analyze configuration files for framework detection."""
        frameworks = set()
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if file_name == 'pom.xml':
                    frameworks.update(self._analyze_maven_pom(content))
                elif file_name in ['package.json']:
                    frameworks.update(self._analyze_package_json(content))
                elif file_name == 'requirements.txt':
                    frameworks.update(self._analyze_requirements_txt(content))
                    
        except Exception as e:
            logger.warning(f"Error reading config file {file_path}: {e}")
        
        return frameworks
    
    def _analyze_maven_pom(self, content: str) -> Set[str]:
        """Analyze Maven POM file for Spring and other frameworks."""
        frameworks = set()
        if 'spring-boot-starter' in content:
            frameworks.add('spring-boot')
        if 'org.springframework' in content:
            frameworks.add('spring')
        if 'hibernate' in content:
            frameworks.add('hibernate')
        if 'junit' in content:
            frameworks.add('junit')
        return frameworks
    
    def _analyze_package_json(self, content: str) -> Set[str]:
        """Analyze package.json for JavaScript frameworks."""
        frameworks = set()
        try:
            data = json.loads(content)
            dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            
            for dep in dependencies:
                if 'react' in dep:
                    frameworks.add('react')
                elif 'angular' in dep or '@angular' in dep:
                    frameworks.add('angular')
                elif 'vue' in dep:
                    frameworks.add('vue')
                elif 'express' in dep:
                    frameworks.add('express')
                elif 'next' in dep:
                    frameworks.add('nextjs')
                    
        except json.JSONDecodeError:
            pass
        return frameworks
    
    def _analyze_requirements_txt(self, content: str) -> Set[str]:
        """Analyze requirements.txt for Python frameworks."""
        frameworks = set()
        lines = content.lower().split('\n')
        for line in lines:
            if 'django' in line:
                frameworks.add('django')
            elif 'flask' in line:
                frameworks.add('flask')
            elif 'fastapi' in line:
                frameworks.add('fastapi')
            elif 'sqlalchemy' in line:
                frameworks.add('sqlalchemy')
        return frameworks
    
    def _analyze_source_file(self, file_path: str) -> Set[str]:
        """Analyze source code files for framework patterns."""
        frameworks = set()
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for framework, patterns in self.FRAMEWORK_INDICATORS.items():
                    if any(pattern in content for pattern in patterns):
                        frameworks.add(framework)
                        
        except Exception as e:
            logger.warning(f"Error reading source file {file_path}: {e}")
        
        return frameworks


class DependencyAnalyzer:
    """Analyzes project dependencies from various build files."""
    
    def analyze_dependencies(self, repo_path: str) -> List[DependencyInfo]:
        """Analyze all dependencies in the repository."""
        dependencies = []
        
        # Maven dependencies
        pom_path = os.path.join(repo_path, 'pom.xml')
        if os.path.exists(pom_path):
            dependencies.extend(self._analyze_maven_dependencies(pom_path))
        
        # NPM dependencies
        package_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_path):
            dependencies.extend(self._analyze_npm_dependencies(package_path))
        
        # Python dependencies
        requirements_path = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            dependencies.extend(self._analyze_pip_dependencies(requirements_path))
        
        return dependencies
    
    def _analyze_maven_dependencies(self, pom_path: str) -> List[DependencyInfo]:
        """Parse Maven POM file for dependencies."""
        dependencies = []
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Handle Maven namespace
            namespace = {'m': 'http://maven.apache.org/POM/4.0.0'}
            
            for dep in root.findall('.//m:dependency', namespace):
                group_id = dep.find('m:groupId', namespace)
                artifact_id = dep.find('m:artifactId', namespace)
                version = dep.find('m:version', namespace)
                scope = dep.find('m:scope', namespace)
                
                if group_id is not None and artifact_id is not None:
                    dep_info = DependencyInfo(
                        name=f"{group_id.text}:{artifact_id.text}",
                        version=version.text if version is not None else None,
                        scope=scope.text if scope is not None else 'compile',
                        type='maven'
                    )
                    dependencies.append(dep_info)
                    
        except Exception as e:
            logger.warning(f"Error parsing Maven POM {pom_path}: {e}")
        
        return dependencies
    
    def _analyze_npm_dependencies(self, package_path: str) -> List[DependencyInfo]:
        """Parse package.json for NPM dependencies."""
        dependencies = []
        try:
            with open(package_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Regular dependencies
                for name, version in data.get('dependencies', {}).items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        scope='runtime',
                        type='npm'
                    ))
                
                # Dev dependencies
                for name, version in data.get('devDependencies', {}).items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        scope='development',
                        type='npm'
                    ))
                    
        except Exception as e:
            logger.warning(f"Error parsing package.json {package_path}: {e}")
        
        return dependencies
    
    def _analyze_pip_dependencies(self, requirements_path: str) -> List[DependencyInfo]:
        """Parse requirements.txt for Python dependencies."""
        dependencies = []
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package==version or package>=version
                        match = re.match(r'^([a-zA-Z0-9\-_.]+)([><=!]+)?([\d.]+.*)?', line)
                        if match:
                            name = match.group(1)
                            version = match.group(3) if match.group(3) else None
                            dependencies.append(DependencyInfo(
                                name=name,
                                version=version,
                                scope='runtime',
                                type='pip'
                            ))
                            
        except Exception as e:
            logger.warning(f"Error parsing requirements.txt {requirements_path}: {e}")
        
        return dependencies


class GitAnalyzer:
    """Analyzes Git repository information."""
    
    def analyze_git_info(self, repo_path: str) -> Optional[GitInfo]:
        """Extract Git information from repository."""
        git_dir = os.path.join(repo_path, '.git')
        if not os.path.exists(git_dir):
            return None
        
        try:
            # Get current branch
            branch = self._run_git_command(['branch', '--show-current'], repo_path).strip()
            
            # Get last commit info
            commit_info = self._run_git_command(['log', '-1', '--format=%H|%ci'], repo_path).strip()
            commit_hash, commit_date_str = commit_info.split('|', 1)
            commit_date = datetime.fromisoformat(commit_date_str.replace(' ', 'T'))
            
            # Get remote URL
            try:
                remote_url = self._run_git_command(['remote', 'get-url', 'origin'], repo_path).strip()
            except:
                remote_url = None
            
            # Check if working directory is dirty
            status = self._run_git_command(['status', '--porcelain'], repo_path)
            is_dirty = bool(status.strip())
            
            return GitInfo(
                branch=branch,
                last_commit=commit_hash,
                last_commit_date=commit_date,
                remote_url=remote_url,
                is_dirty=is_dirty
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing Git info for {repo_path}: {e}")
            return None
    
    def _run_git_command(self, args: List[str], repo_path: str) -> str:
        """Run a git command in the specified repository."""
        cmd = ['git'] + args
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Git command failed: {result.stderr}")
        
        return result.stdout


class RepositoryScanner:
    """Main repository scanner that orchestrates all analysis components."""
    
    def __init__(self, base_path: str, cache_dir: str = ".repo_cache"):
        self.base_path = Path(base_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.language_detector = LanguageDetector()
        self.dependency_analyzer = DependencyAnalyzer()
        self.git_analyzer = GitAnalyzer()
        
        self._cache = {}
        self._load_cache()
    
    async def scan_repositories(self, force_rescan: bool = False) -> List[RepositoryInfo]:
        """Scan all repositories in the base path."""
        logger.info(f"Starting repository scan in {self.base_path}")
        start_time = datetime.now()
        
        # Discover repository directories
        repo_paths = self._discover_repositories()
        logger.info(f"Found {len(repo_paths)} repositories")
        
        # Scan repositories in parallel
        tasks = []
        for repo_path in repo_paths:
            task = self._scan_single_repository(repo_path, force_rescan)
            tasks.append(task)
        
        # Execute scans with limited concurrency
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent scans
        results = []
        
        async def scan_with_semaphore(task):
            async with semaphore:
                return await task
        
        for coro in asyncio.as_completed([scan_with_semaphore(task) for task in tasks]):
            try:
                result = await coro
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error scanning repository: {e}")
        
        # Save cache
        self._save_cache()
        
        scan_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Repository scan completed in {scan_duration:.2f} seconds")
        
        return results
    
    def _discover_repositories(self) -> List[Path]:
        """Discover all Git repositories in the base path."""
        repo_paths = []
        
        for item in self.base_path.iterdir():
            if item.is_dir():
                git_dir = item / '.git'
                if git_dir.exists():
                    repo_paths.append(item)
                else:
                    # Check subdirectories for repositories
                    for subitem in item.iterdir():
                        if subitem.is_dir() and (subitem / '.git').exists():
                            repo_paths.append(subitem)
        
        return repo_paths
    
    async def _scan_single_repository(self, repo_path: Path, force_rescan: bool) -> Optional[RepositoryInfo]:
        """Scan a single repository."""
        repo_name = repo_path.name
        cache_key = str(repo_path)
        
        # Check cache
        if not force_rescan and cache_key in self._cache:
            cached_info = self._cache[cache_key]
            cache_age = datetime.now() - cached_info.last_scanned
            if cache_age < timedelta(hours=1):  # Cache for 1 hour
                logger.debug(f"Using cached data for {repo_name}")
                return cached_info
        
        logger.info(f"Scanning repository: {repo_name}")
        start_time = datetime.now()
        
        try:
            # Run analysis in thread pool for CPU-intensive work
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                repo_info = await loop.run_in_executor(
                    executor, 
                    self._analyze_repository, 
                    repo_path
                )
            
            scan_duration = (datetime.now() - start_time).total_seconds()
            repo_info.scan_duration = scan_duration
            
            # Cache the result
            self._cache[cache_key] = repo_info
            
            logger.info(f"Completed scanning {repo_name} in {scan_duration:.2f}s")
            return repo_info
            
        except Exception as e:
            logger.error(f"Error scanning repository {repo_name}: {e}")
            return None
    
    def _analyze_repository(self, repo_path: Path) -> RepositoryInfo:
        """Perform detailed analysis of a repository."""
        # Scan file structure
        file_infos = self._scan_files(repo_path)
        
        # Detect languages
        languages = self._detect_languages(file_infos)
        primary_language = max(languages, key=languages.get) if languages else 'unknown'
        
        # Detect frameworks
        frameworks = self.language_detector.detect_frameworks(str(repo_path), file_infos)
        
        # Analyze dependencies
        dependencies = self.dependency_analyzer.analyze_dependencies(str(repo_path))
        
        # Get Git information
        git_info = self.git_analyzer.analyze_git_info(str(repo_path))
        
        # Calculate repository size
        total_size = sum(f.size for f in file_infos)
        
        # Build file structure
        file_structure = self._build_file_structure(file_infos)
        
        return RepositoryInfo(
            name=repo_path.name,
            path=str(repo_path),
            primary_language=primary_language,
            languages=list(languages.keys()),
            frameworks=frameworks,
            dependencies=dependencies,
            file_structure=file_structure,
            git_info=git_info,
            size_bytes=total_size,
            file_count=len(file_infos),
            last_scanned=datetime.now(),
            scan_duration=0.0  # Will be set by caller
        )
    
    def _scan_files(self, repo_path: Path) -> List[FileInfo]:
        """Scan all files in the repository."""
        file_infos = []
        
        # Skip common directories that don't contain source code
        skip_dirs = {'.git', 'node_modules', 'target', 'build', 'dist', '.vscode', '.idea', '__pycache__'}
        
        for root, dirs, files in os.walk(repo_path):
            # Remove skip directories from dirs to avoid walking them
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                
                try:
                    stat = os.stat(file_path)
                    language = self.language_detector.detect_language(file_path)
                    
                    file_info = FileInfo(
                        path=relative_path,
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime),
                        language=language,
                        is_config=self._is_config_file(file),
                        is_test=self._is_test_file(relative_path)
                    )
                    file_infos.append(file_info)
                    
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
        
        return file_infos
    
    def _detect_languages(self, file_infos: List[FileInfo]) -> Dict[str, int]:
        """Count files by programming language."""
        language_counts = {}
        
        for file_info in file_infos:
            if file_info.language:
                language_counts[file_info.language] = language_counts.get(file_info.language, 0) + 1
        
        return language_counts
    
    def _is_config_file(self, filename: str) -> bool:
        """Check if a file is a configuration file."""
        config_patterns = [
            'config', '.properties', '.yml', '.yaml', '.json', '.xml', 
            '.env', 'Dockerfile', 'docker-compose', '.gitignore', 'README'
        ]
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in config_patterns)
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file."""
        test_indicators = ['test', 'spec', '__tests__', 'tests']
        path_lower = file_path.lower()
        return any(indicator in path_lower for indicator in test_indicators)
    
    def _build_file_structure(self, file_infos: List[FileInfo]) -> Dict[str, Any]:
        """Build a hierarchical file structure."""
        structure = {}
        
        for file_info in file_infos:
            parts = file_info.path.split(os.sep)
            current = structure
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # This is a file
                    current[part] = {
                        'type': 'file',
                        'size': file_info.size,
                        'language': file_info.language,
                        'is_config': file_info.is_config,
                        'is_test': file_info.is_test
                    }
                else:  # This is a directory
                    if part not in current:
                        current[part] = {'type': 'directory', 'children': {}}
                    current = current[part]['children']
        
        return structure
    
    def _load_cache(self):
        """Load repository cache from disk."""
        cache_file = self.cache_dir / 'repository_cache.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                # Convert cache data back to RepositoryInfo objects
                for key, data in cache_data.items():
                    # Convert datetime strings back to datetime objects
                    data['last_scanned'] = datetime.fromisoformat(data['last_scanned'])
                    if data.get('git_info') and data['git_info'].get('last_commit_date'):
                        data['git_info']['last_commit_date'] = datetime.fromisoformat(data['git_info']['last_commit_date'])
                    
                    # Convert back to dataclass
                    dependencies = [DependencyInfo(**dep) for dep in data.get('dependencies', [])]
                    git_info = GitInfo(**data['git_info']) if data.get('git_info') else None
                    
                    self._cache[key] = RepositoryInfo(
                        name=data['name'],
                        path=data['path'],
                        primary_language=data['primary_language'],
                        languages=data['languages'],
                        frameworks=data['frameworks'],
                        dependencies=dependencies,
                        file_structure=data['file_structure'],
                        git_info=git_info,
                        size_bytes=data['size_bytes'],
                        file_count=data['file_count'],
                        last_scanned=data['last_scanned'],
                        scan_duration=data['scan_duration']
                    )
                    
                logger.info(f"Loaded cache with {len(self._cache)} repositories")
                
            except Exception as e:
                logger.warning(f"Error loading cache: {e}")
                self._cache = {}
    
    def _save_cache(self):
        """Save repository cache to disk."""
        cache_file = self.cache_dir / 'repository_cache.json'
        try:
            # Convert cache to JSON-serializable format
            cache_data = {}
            for key, repo_info in self._cache.items():
                data = asdict(repo_info)
                # Convert datetime objects to strings
                data['last_scanned'] = data['last_scanned'].isoformat()
                if data.get('git_info') and data['git_info'].get('last_commit_date'):
                    data['git_info']['last_commit_date'] = data['git_info']['last_commit_date'].isoformat()
                cache_data[key] = data
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved cache with {len(cache_data)} repositories")
            
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def search_code_patterns(self, pattern: str, repo_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for code patterns across repositories."""
        results = []
        
        # Filter repositories if specified
        target_repos = []
        if repo_names:
            target_repos = [repo for repo in self._cache.values() if repo.name in repo_names]
        else:
            target_repos = list(self._cache.values())
        
        for repo_info in target_repos:
            repo_results = self._search_in_repository(pattern, repo_info)
            results.extend(repo_results)
        
        return results
    
    def _search_in_repository(self, pattern: str, repo_info: RepositoryInfo) -> List[Dict[str, Any]]:
        """Search for a pattern in a specific repository."""
        results = []
        repo_path = Path(repo_info.path)
        
        # Only search in source code files
        source_extensions = {'.java', '.py', '.js', '.ts', '.jsx', '.tsx', '.cs', '.cpp', '.c', '.go', '.rs'}
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'target', 'build'}]
                
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext.lower() in source_extensions:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            # Search for pattern (simple string search for now)
                            lines = content.split('\n')
                            for line_num, line in enumerate(lines, 1):
                                if pattern.lower() in line.lower():
                                    results.append({
                                        'repository': repo_info.name,
                                        'file_path': relative_path,
                                        'line_number': line_num,
                                        'line_content': line.strip(),
                                        'pattern': pattern
                                    })
                                    
                        except Exception as e:
                            logger.debug(f"Error searching in {file_path}: {e}")
                            
        except Exception as e:
            logger.warning(f"Error searching repository {repo_info.name}: {e}")
        
        return results
    
    def get_repository_by_name(self, name: str) -> Optional[RepositoryInfo]:
        """Get repository information by name."""
        for repo_info in self._cache.values():
            if repo_info.name == name:
                return repo_info
        return None
    
    def get_file_content(self, repo_name: str, file_path: str) -> Optional[str]:
        """Get the content of a specific file in a repository."""
        repo_info = self.get_repository_by_name(repo_name)
        if not repo_info:
            return None
        
        full_path = os.path.join(repo_info.path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Error reading file {full_path}: {e}")
            return None


# Example usage
async def main():
    """Example usage of the repository scanner."""
    scanner = RepositoryScanner("/path/to/repositories")
    
    # Scan all repositories
    repositories = await scanner.scan_repositories()
    
    # Print summary
    print(f"Scanned {len(repositories)} repositories:")
    for repo in repositories:
        print(f"  {repo.name}: {repo.primary_language}, {repo.file_count} files, {len(repo.frameworks)} frameworks")
    
    # Search for patterns
    results = scanner.search_code_patterns("@RestController")
    print(f"Found {len(results)} matches for @RestController")


if __name__ == "__main__":
    asyncio.run(main())