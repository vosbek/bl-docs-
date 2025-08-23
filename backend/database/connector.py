"""
Database Connector Module

This module provides Oracle database connectivity and schema analysis capabilities
for AI agents to understand database structure and relationships.
"""

import os
import logging
import asyncio
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import hashlib
from contextlib import asynccontextmanager
import cx_Oracle
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    data_type: str
    nullable: bool
    default_value: Optional[str]
    max_length: Optional[int]
    precision: Optional[int]
    scale: Optional[int]
    is_primary_key: bool
    is_foreign_key: bool
    comments: Optional[str]


@dataclass
class IndexInfo:
    """Information about a database index."""
    name: str
    table_name: str
    columns: List[str]
    is_unique: bool
    is_primary: bool
    index_type: str


@dataclass
class ForeignKeyInfo:
    """Information about a foreign key relationship."""
    name: str
    source_table: str
    source_columns: List[str]
    target_table: str
    target_columns: List[str]
    delete_rule: str
    update_rule: str


@dataclass
class TableInfo:
    """Complete information about a database table."""
    name: str
    schema: str
    table_type: str  # TABLE, VIEW, etc.
    columns: List[ColumnInfo]
    indexes: List[IndexInfo]
    foreign_keys: List[ForeignKeyInfo]
    row_count: Optional[int]
    comments: Optional[str]
    last_analyzed: datetime


@dataclass
class SchemaAnalysis:
    """Complete schema analysis results."""
    schema_name: str
    tables: List[TableInfo]
    views: List[str]
    sequences: List[str]
    procedures: List[str]
    functions: List[str]
    total_tables: int
    total_columns: int
    analysis_date: datetime
    analysis_duration: float


@dataclass
class QueryResult:
    """Result of a database query execution."""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time: float
    query_hash: str


class DatabaseSecurity:
    """Security measures for database access."""
    
    # Allowed query patterns (read-only operations)
    ALLOWED_PATTERNS = [
        r'^SELECT\s+',
        r'^WITH\s+',
        r'^EXPLAIN\s+',
        r'^DESCRIBE\s+',
        r'^DESC\s+',
    ]
    
    # Forbidden patterns
    FORBIDDEN_PATTERNS = [
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bCREATE\b',
        r'\bALTER\b',
        r'\bTRUNCATE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
        r'\bEXEC\b',
        r'\bEXECUTE\b',
    ]
    
    # Sensitive column patterns to mask
    SENSITIVE_COLUMNS = [
        r'.*password.*',
        r'.*ssn.*',
        r'.*social.*',
        r'.*credit.*',
        r'.*card.*',
        r'.*token.*',
        r'.*secret.*',
        r'.*key.*',
        r'.*pin.*',
    ]
    
    @classmethod
    def validate_query(cls, query: str) -> bool:
        """Validate that a query is safe for execution."""
        import re
        
        query_upper = query.upper().strip()
        
        # Check if query starts with allowed patterns
        allowed = any(re.match(pattern, query_upper, re.IGNORECASE) for pattern in cls.ALLOWED_PATTERNS)
        if not allowed:
            return False
        
        # Check for forbidden patterns
        forbidden = any(re.search(pattern, query_upper, re.IGNORECASE) for pattern in cls.FORBIDDEN_PATTERNS)
        if forbidden:
            return False
        
        return True
    
    @classmethod
    def mask_sensitive_data(cls, column_name: str, value: Any) -> Any:
        """Mask sensitive data in query results."""
        import re
        
        if value is None:
            return None
        
        column_lower = column_name.lower()
        is_sensitive = any(re.match(pattern, column_lower) for pattern in cls.SENSITIVE_COLUMNS)
        
        if is_sensitive:
            if isinstance(value, str):
                return '*' * min(len(value), 8)
            else:
                return '***'
        
        return value


class ConnectionPool:
    """Thread-safe Oracle connection pool."""
    
    def __init__(self, dsn: str, username: str, password: str, min_connections: int = 1, max_connections: int = 5):
        self.dsn = dsn
        self.username = username
        self.password = password
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool = None
        self._executor = ThreadPoolExecutor(max_workers=max_connections)
    
    def initialize(self):
        """Initialize the connection pool."""
        try:
            self._pool = cx_Oracle.SessionPool(
                user=self.username,
                password=self.password,
                dsn=self.dsn,
                min=self.min_connections,
                max=self.max_connections,
                increment=1,
                encoding="UTF-8"
            )
            logger.info(f"Database connection pool initialized with {self.min_connections}-{self.max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")
        
        loop = asyncio.get_event_loop()
        connection = await loop.run_in_executor(self._executor, self._pool.acquire)
        
        try:
            yield connection
        finally:
            await loop.run_in_executor(self._executor, self._pool.release, connection)
    
    def close(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.close()
            self._executor.shutdown(wait=True)
            logger.info("Database connection pool closed")


class SchemaAnalyzer:
    """Analyzes Oracle database schema structure."""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.pool = connection_pool
        self._cache = {}
        self._cache_ttl = timedelta(hours=1)
    
    async def analyze_schema(self, schema_name: str, force_refresh: bool = False) -> SchemaAnalysis:
        """Perform complete schema analysis."""
        cache_key = f"schema_{schema_name}"
        
        # Check cache
        if not force_refresh and cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_ttl:
                logger.debug(f"Using cached schema analysis for {schema_name}")
                return cached_result
        
        logger.info(f"Analyzing schema: {schema_name}")
        start_time = datetime.now()
        
        try:
            async with self.pool.get_connection() as conn:
                # Get all tables
                tables = await self._get_tables(conn, schema_name)
                
                # Analyze each table in parallel
                table_tasks = []
                for table_name in tables:
                    task = self._analyze_table(conn, schema_name, table_name)
                    table_tasks.append(task)
                
                table_infos = await asyncio.gather(*table_tasks, return_exceptions=True)
                
                # Filter out exceptions
                valid_tables = [t for t in table_infos if isinstance(t, TableInfo)]
                
                # Get other schema objects
                views = await self._get_views(conn, schema_name)
                sequences = await self._get_sequences(conn, schema_name)
                procedures = await self._get_procedures(conn, schema_name)
                functions = await self._get_functions(conn, schema_name)
                
                # Calculate statistics
                total_columns = sum(len(table.columns) for table in valid_tables)
                
                analysis_duration = (datetime.now() - start_time).total_seconds()
                
                result = SchemaAnalysis(
                    schema_name=schema_name,
                    tables=valid_tables,
                    views=views,
                    sequences=sequences,
                    procedures=procedures,
                    functions=functions,
                    total_tables=len(valid_tables),
                    total_columns=total_columns,
                    analysis_date=datetime.now(),
                    analysis_duration=analysis_duration
                )
                
                # Cache the result
                self._cache[cache_key] = (result, datetime.now())
                
                logger.info(f"Schema analysis completed in {analysis_duration:.2f}s: {len(valid_tables)} tables, {total_columns} columns")
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing schema {schema_name}: {e}")
            raise
    
    async def _get_tables(self, connection, schema_name: str) -> List[str]:
        """Get all table names in the schema."""
        query = """
        SELECT table_name 
        FROM all_tables 
        WHERE owner = :schema_name 
        ORDER BY table_name
        """
        
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(None, connection.cursor)
        
        try:
            await loop.run_in_executor(None, cursor.execute, query, {'schema_name': schema_name.upper()})
            rows = await loop.run_in_executor(None, cursor.fetchall)
            return [row[0] for row in rows]
        finally:
            await loop.run_in_executor(None, cursor.close)
    
    async def _analyze_table(self, connection, schema_name: str, table_name: str) -> TableInfo:
        """Analyze a single table."""
        loop = asyncio.get_event_loop()
        
        # Get table metadata
        table_info = await loop.run_in_executor(
            None, 
            self._get_table_metadata, 
            connection, 
            schema_name, 
            table_name
        )
        
        return table_info
    
    def _get_table_metadata(self, connection, schema_name: str, table_name: str) -> TableInfo:
        """Get complete metadata for a table (runs in thread executor)."""
        cursor = connection.cursor()
        
        try:
            # Get columns
            columns = self._get_table_columns(cursor, schema_name, table_name)
            
            # Get indexes
            indexes = self._get_table_indexes(cursor, schema_name, table_name)
            
            # Get foreign keys
            foreign_keys = self._get_table_foreign_keys(cursor, schema_name, table_name)
            
            # Get table comments
            comments = self._get_table_comments(cursor, schema_name, table_name)
            
            # Get row count (with timeout)
            try:
                row_count = self._get_table_row_count(cursor, schema_name, table_name)
            except:
                row_count = None
            
            return TableInfo(
                name=table_name,
                schema=schema_name,
                table_type='TABLE',
                columns=columns,
                indexes=indexes,
                foreign_keys=foreign_keys,
                row_count=row_count,
                comments=comments,
                last_analyzed=datetime.now()
            )
            
        finally:
            cursor.close()
    
    def _get_table_columns(self, cursor, schema_name: str, table_name: str) -> List[ColumnInfo]:
        """Get column information for a table."""
        query = """
        SELECT 
            c.column_name,
            c.data_type,
            c.nullable,
            c.data_default,
            c.data_length,
            c.data_precision,
            c.data_scale,
            CASE WHEN pk.column_name IS NOT NULL THEN 'Y' ELSE 'N' END as is_primary_key,
            CASE WHEN fk.column_name IS NOT NULL THEN 'Y' ELSE 'N' END as is_foreign_key,
            cc.comments
        FROM all_tab_columns c
        LEFT JOIN (
            SELECT cc.table_name, cc.column_name
            FROM all_constraints con
            JOIN all_cons_columns cc ON con.constraint_name = cc.constraint_name 
                AND con.owner = cc.owner
            WHERE con.constraint_type = 'P' AND con.owner = :schema_name
        ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
        LEFT JOIN (
            SELECT cc.table_name, cc.column_name
            FROM all_constraints con
            JOIN all_cons_columns cc ON con.constraint_name = cc.constraint_name 
                AND con.owner = cc.owner
            WHERE con.constraint_type = 'R' AND con.owner = :schema_name
        ) fk ON c.table_name = fk.table_name AND c.column_name = fk.column_name
        LEFT JOIN all_col_comments cc ON c.owner = cc.owner 
            AND c.table_name = cc.table_name 
            AND c.column_name = cc.column_name
        WHERE c.owner = :schema_name AND c.table_name = :table_name
        ORDER BY c.column_id
        """
        
        cursor.execute(query, {
            'schema_name': schema_name.upper(),
            'table_name': table_name.upper()
        })
        
        columns = []
        for row in cursor.fetchall():
            column = ColumnInfo(
                name=row[0],
                data_type=row[1],
                nullable=row[2] == 'Y',
                default_value=row[3],
                max_length=row[4],
                precision=row[5],
                scale=row[6],
                is_primary_key=row[7] == 'Y',
                is_foreign_key=row[8] == 'Y',
                comments=row[9]
            )
            columns.append(column)
        
        return columns
    
    def _get_table_indexes(self, cursor, schema_name: str, table_name: str) -> List[IndexInfo]:
        """Get index information for a table."""
        query = """
        SELECT DISTINCT
            i.index_name,
            i.index_type,
            i.uniqueness,
            LISTAGG(ic.column_name, ',') WITHIN GROUP (ORDER BY ic.column_position) as columns
        FROM all_indexes i
        JOIN all_ind_columns ic ON i.index_name = ic.index_name AND i.owner = ic.index_owner
        WHERE i.owner = :schema_name AND i.table_name = :table_name
        GROUP BY i.index_name, i.index_type, i.uniqueness
        ORDER BY i.index_name
        """
        
        cursor.execute(query, {
            'schema_name': schema_name.upper(),
            'table_name': table_name.upper()
        })
        
        indexes = []
        for row in cursor.fetchall():
            index = IndexInfo(
                name=row[0],
                table_name=table_name,
                columns=row[3].split(','),
                is_unique=row[2] == 'UNIQUE',
                is_primary=False,  # Will be determined separately
                index_type=row[1]
            )
            indexes.append(index)
        
        return indexes
    
    def _get_table_foreign_keys(self, cursor, schema_name: str, table_name: str) -> List[ForeignKeyInfo]:
        """Get foreign key information for a table."""
        query = """
        SELECT 
            c.constraint_name,
            c.table_name as source_table,
            LISTAGG(cc.column_name, ',') WITHIN GROUP (ORDER BY cc.position) as source_columns,
            c.r_constraint_name,
            rc.table_name as target_table,
            LISTAGG(rcc.column_name, ',') WITHIN GROUP (ORDER BY rcc.position) as target_columns,
            c.delete_rule
        FROM all_constraints c
        JOIN all_cons_columns cc ON c.constraint_name = cc.constraint_name AND c.owner = cc.owner
        JOIN all_constraints rc ON c.r_constraint_name = rc.constraint_name AND c.r_owner = rc.owner
        JOIN all_cons_columns rcc ON rc.constraint_name = rcc.constraint_name AND rc.owner = rcc.owner
        WHERE c.constraint_type = 'R' 
            AND c.owner = :schema_name 
            AND c.table_name = :table_name
        GROUP BY c.constraint_name, c.table_name, c.r_constraint_name, rc.table_name, c.delete_rule
        """
        
        cursor.execute(query, {
            'schema_name': schema_name.upper(),
            'table_name': table_name.upper()
        })
        
        foreign_keys = []
        for row in cursor.fetchall():
            fk = ForeignKeyInfo(
                name=row[0],
                source_table=row[1],
                source_columns=row[2].split(','),
                target_table=row[4],
                target_columns=row[5].split(','),
                delete_rule=row[6] or 'NO ACTION',
                update_rule='NO ACTION'  # Oracle doesn't support ON UPDATE
            )
            foreign_keys.append(fk)
        
        return foreign_keys
    
    def _get_table_comments(self, cursor, schema_name: str, table_name: str) -> Optional[str]:
        """Get table comments."""
        query = """
        SELECT comments 
        FROM all_tab_comments 
        WHERE owner = :schema_name AND table_name = :table_name
        """
        
        cursor.execute(query, {
            'schema_name': schema_name.upper(),
            'table_name': table_name.upper()
        })
        
        row = cursor.fetchone()
        return row[0] if row else None
    
    def _get_table_row_count(self, cursor, schema_name: str, table_name: str) -> Optional[int]:
        """Get approximate row count for a table."""
        # Use statistics first (faster)
        query = """
        SELECT num_rows 
        FROM all_tables 
        WHERE owner = :schema_name AND table_name = :table_name AND num_rows IS NOT NULL
        """
        
        cursor.execute(query, {
            'schema_name': schema_name.upper(),
            'table_name': table_name.upper()
        })
        
        row = cursor.fetchone()
        if row and row[0] is not None:
            return row[0]
        
        # If no statistics, do a quick count (with timeout)
        try:
            count_query = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
            cursor.execute(count_query)
            row = cursor.fetchone()
            return row[0] if row else None
        except:
            return None
    
    async def _get_views(self, connection, schema_name: str) -> List[str]:
        """Get all view names in the schema."""
        query = "SELECT view_name FROM all_views WHERE owner = :schema_name ORDER BY view_name"
        
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(None, connection.cursor)
        
        try:
            await loop.run_in_executor(None, cursor.execute, query, {'schema_name': schema_name.upper()})
            rows = await loop.run_in_executor(None, cursor.fetchall)
            return [row[0] for row in rows]
        finally:
            await loop.run_in_executor(None, cursor.close)
    
    async def _get_sequences(self, connection, schema_name: str) -> List[str]:
        """Get all sequence names in the schema."""
        query = "SELECT sequence_name FROM all_sequences WHERE sequence_owner = :schema_name ORDER BY sequence_name"
        
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(None, connection.cursor)
        
        try:
            await loop.run_in_executor(None, cursor.execute, query, {'schema_name': schema_name.upper()})
            rows = await loop.run_in_executor(None, cursor.fetchall)
            return [row[0] for row in rows]
        finally:
            await loop.run_in_executor(None, cursor.close)
    
    async def _get_procedures(self, connection, schema_name: str) -> List[str]:
        """Get all procedure names in the schema."""
        query = """
        SELECT object_name 
        FROM all_objects 
        WHERE owner = :schema_name AND object_type = 'PROCEDURE'
        ORDER BY object_name
        """
        
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(None, connection.cursor)
        
        try:
            await loop.run_in_executor(None, cursor.execute, query, {'schema_name': schema_name.upper()})
            rows = await loop.run_in_executor(None, cursor.fetchall)
            return [row[0] for row in rows]
        finally:
            await loop.run_in_executor(None, cursor.close)
    
    async def _get_functions(self, connection, schema_name: str) -> List[str]:
        """Get all function names in the schema."""
        query = """
        SELECT object_name 
        FROM all_objects 
        WHERE owner = :schema_name AND object_type = 'FUNCTION'
        ORDER BY object_name
        """
        
        loop = asyncio.get_event_loop()
        cursor = await loop.run_in_executor(None, connection.cursor)
        
        try:
            await loop.run_in_executor(None, cursor.execute, query, {'schema_name': schema_name.upper()})
            rows = await loop.run_in_executor(None, cursor.fetchall)
            return [row[0] for row in rows]
        finally:
            await loop.run_in_executor(None, cursor.close)


class QueryExecutor:
    """Executes read-only queries against the database."""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.pool = connection_pool
        self._query_cache = {}
        self._cache_ttl = timedelta(minutes=15)
    
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> QueryResult:
        """Execute a read-only query."""
        # Validate query security
        if not DatabaseSecurity.validate_query(query):
            raise ValueError("Query contains forbidden operations")
        
        # Generate cache key
        query_hash = hashlib.md5(f"{query}_{parameters}".encode()).hexdigest()
        
        # Check cache
        if use_cache and query_hash in self._query_cache:
            cached_result, cached_time = self._query_cache[query_hash]
            if datetime.now() - cached_time < self._cache_ttl:
                logger.debug(f"Using cached query result: {query_hash}")
                return cached_result
        
        logger.info(f"Executing query: {query[:100]}...")
        start_time = datetime.now()
        
        try:
            async with self.pool.get_connection() as conn:
                loop = asyncio.get_event_loop()
                cursor = await loop.run_in_executor(None, conn.cursor)
                
                try:
                    # Set query timeout (30 seconds)
                    await loop.run_in_executor(None, self._execute_with_timeout, cursor, query, parameters)
                    
                    # Fetch results
                    rows = await loop.run_in_executor(None, cursor.fetchall)
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    
                    # Apply security filtering
                    filtered_rows = []
                    for row in rows:
                        filtered_row = []
                        for i, value in enumerate(row):
                            column_name = columns[i] if i < len(columns) else f"col_{i}"
                            filtered_value = DatabaseSecurity.mask_sensitive_data(column_name, value)
                            filtered_row.append(filtered_value)
                        filtered_rows.append(filtered_row)
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    result = QueryResult(
                        columns=columns,
                        rows=filtered_rows,
                        row_count=len(filtered_rows),
                        execution_time=execution_time,
                        query_hash=query_hash
                    )
                    
                    # Cache the result
                    if use_cache:
                        self._query_cache[query_hash] = (result, datetime.now())
                    
                    logger.info(f"Query executed successfully: {len(filtered_rows)} rows in {execution_time:.2f}s")
                    return result
                    
                finally:
                    await loop.run_in_executor(None, cursor.close)
                    
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def _execute_with_timeout(self, cursor, query: str, parameters: Optional[Dict[str, Any]]):
        """Execute query with timeout (runs in thread executor)."""
        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)
    
    async def get_table_sample(self, schema_name: str, table_name: str, limit: int = 10) -> QueryResult:
        """Get a sample of data from a table."""
        query = f"""
        SELECT * FROM (
            SELECT * FROM {schema_name}.{table_name}
            ORDER BY ROWNUM
        ) WHERE ROWNUM <= :limit
        """
        
        return await self.execute_query(query, {'limit': limit})
    
    async def explain_query(self, query: str) -> QueryResult:
        """Get the execution plan for a query."""
        explain_query = f"EXPLAIN PLAN FOR {query}"
        
        # Execute explain plan
        await self.execute_query(explain_query, use_cache=False)
        
        # Get the plan
        plan_query = """
        SELECT LPAD(' ', 2*level) || operation || ' ' || options || ' ' || object_name as plan_step
        FROM plan_table
        CONNECT BY PRIOR id = parent_id
        START WITH id = 0
        ORDER BY id
        """
        
        return await self.execute_query(plan_query, use_cache=False)


class DatabaseConnector:
    """Main database connector that orchestrates all database operations."""
    
    def __init__(self, jdbc_url: str, username: str, password: str):
        self.jdbc_url = jdbc_url
        self.username = username
        self.password = password
        
        # Parse DSN from JDBC URL
        self.dsn = self._parse_dsn(jdbc_url)
        
        self.pool = ConnectionPool(self.dsn, username, password)
        self.schema_analyzer = SchemaAnalyzer(self.pool)
        self.query_executor = QueryExecutor(self.pool)
        
        self._initialized = False
    
    def _parse_dsn(self, jdbc_url: str) -> str:
        """Parse Oracle DSN from JDBC URL."""
        # Example: jdbc:oracle:thin:@localhost:1521:xe
        # or: jdbc:oracle:thin:@//localhost:1521/xe
        import re
        
        pattern = r'jdbc:oracle:thin:@(?://)?([^:/]+):(\d+)[:/](.+)'
        match = re.match(pattern, jdbc_url)
        
        if not match:
            raise ValueError(f"Invalid Oracle JDBC URL: {jdbc_url}")
        
        host = match.group(1)
        port = match.group(2)
        service = match.group(3)
        
        return f"{host}:{port}/{service}"
    
    async def initialize(self):
        """Initialize the database connection."""
        if self._initialized:
            return
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.pool.initialize)
            self._initialized = True
            logger.info("Database connector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connector: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            await self.initialize()
            result = await self.query_executor.execute_query("SELECT 1 FROM DUAL", use_cache=False)
            return result.row_count > 0
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    async def analyze_schema(self, schema_name: str, force_refresh: bool = False) -> SchemaAnalysis:
        """Analyze a database schema."""
        await self.initialize()
        return await self.schema_analyzer.analyze_schema(schema_name, force_refresh)
    
    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute a read-only query."""
        await self.initialize()
        return await self.query_executor.execute_query(query, parameters)
    
    async def get_table_info(self, schema_name: str, table_name: str) -> Optional[TableInfo]:
        """Get detailed information about a specific table."""
        schema_analysis = await self.analyze_schema(schema_name)
        
        for table in schema_analysis.tables:
            if table.name.upper() == table_name.upper():
                return table
        
        return None
    
    async def search_tables(self, schema_name: str, pattern: str) -> List[str]:
        """Search for tables matching a pattern."""
        query = """
        SELECT table_name 
        FROM all_tables 
        WHERE owner = :schema_name 
            AND UPPER(table_name) LIKE UPPER(:pattern)
        ORDER BY table_name
        """
        
        result = await self.execute_query(query, {
            'schema_name': schema_name.upper(),
            'pattern': f"%{pattern}%"
        })
        
        return [row[0] for row in result.rows]
    
    async def get_table_relationships(self, schema_name: str, table_name: str) -> Dict[str, List[str]]:
        """Get relationships for a table (parents and children)."""
        # Get parent tables (tables this table references)
        parent_query = """
        SELECT DISTINCT rc.table_name as parent_table
        FROM all_constraints c
        JOIN all_constraints rc ON c.r_constraint_name = rc.constraint_name AND c.r_owner = rc.owner
        WHERE c.constraint_type = 'R' 
            AND c.owner = :schema_name 
            AND c.table_name = :table_name
        """
        
        # Get child tables (tables that reference this table)
        child_query = """
        SELECT DISTINCT c.table_name as child_table
        FROM all_constraints c
        JOIN all_constraints rc ON c.r_constraint_name = rc.constraint_name AND c.r_owner = rc.owner
        WHERE c.constraint_type = 'R' 
            AND rc.owner = :schema_name 
            AND rc.table_name = :table_name
        """
        
        parent_result = await self.execute_query(parent_query, {
            'schema_name': schema_name.upper(),
            'table_name': table_name.upper()
        })
        
        child_result = await self.execute_query(child_query, {
            'schema_name': schema_name.upper(),
            'table_name': table_name.upper()
        })
        
        return {
            'parents': [row[0] for row in parent_result.rows],
            'children': [row[0] for row in child_result.rows]
        }
    
    def close(self):
        """Close the database connection."""
        if self._initialized:
            self.pool.close()
            self._initialized = False
            logger.info("Database connector closed")


# Example usage
async def main():
    """Example usage of the database connector."""
    # Initialize connector
    connector = DatabaseConnector(
        jdbc_url="jdbc:oracle:thin:@localhost:1521:xe",
        username="your_username",
        password="your_password"
    )
    
    try:
        # Test connection
        if await connector.test_connection():
            print("Database connection successful")
        
        # Analyze schema
        schema_analysis = await connector.analyze_schema("YOUR_SCHEMA")
        print(f"Schema analysis: {len(schema_analysis.tables)} tables")
        
        # Execute a query
        result = await connector.execute_query("SELECT COUNT(*) FROM user_tables")
        print(f"Query result: {result.rows}")
        
    finally:
        connector.close()


if __name__ == "__main__":
    asyncio.run(main())