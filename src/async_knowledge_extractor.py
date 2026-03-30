#!/usr/bin/env python3
"""
Enhanced Async Knowledge Extractor - Comprehensive Codebase Scanner

Features:
- Fully async background processing with multiprocessing
- Custom output location for Komposteur project
- Comprehensive scanning of ALL source files (no 15-20 file limit)
- Enhanced reporting with navigation indices
- Progress monitoring and resume capability
- Error resilience for JSON parsing
- Database in target project directory
"""

import json
import sqlite3
import hashlib
import time
import asyncio
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import os
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from collections import defaultdict
import uuid

# Optional imports with fallbacks
try:
    import networkx as nx
except ImportError:
    class _DummyNX:
        Graph = None
    nx = _DummyNX()

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

@dataclass
class AsyncExtractionResult:
    """Results from async knowledge extraction"""
    file_path: str
    content_hash: str
    entities: List[Dict[str, str]]
    relationships: List[Dict[str, str]]
    summary: str
    confidence: float
    processing_time: float
    token_usage: int
    cost_estimate: float
    completion_status: str
    error_info: Optional[str] = None
    file_size_bytes: int = 0
    line_count: int = 0

@dataclass
class ProgressState:
    """Progress tracking for long-running extractions"""
    session_id: str
    total_files: int
    completed_files: int
    failed_files: int
    start_time: float
    estimated_completion: Optional[float] = None
    current_file: Optional[str] = None
    phase: str = "initializing"  # initializing, scanning, processing, indexing, reporting

@dataclass
class NavigationIndex:
    """Navigation index for easy codebase exploration"""
    classes: Dict[str, List[str]]  # class_name -> [file_paths]
    functions: Dict[str, List[str]]  # function_name -> [file_paths]
    packages: Dict[str, List[str]]   # package_name -> [file_paths]
    technologies: Set[str]           # detected technologies
    file_types: Dict[str, int]       # extension -> count
    dependency_graph: Dict[str, List[str]]  # file -> dependencies

class AsyncLightweightGraphDB:
    """SQLite-based lightweight graph database with async operations"""
    
    def __init__(self, db_path: str = "knowledge_graph.db"):
        self.db_path = db_path
        self.setup_schema()
    
    def get_connection(self):
        """Get a new database connection (for thread safety)"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def setup_schema(self):
        """Create database schema for graph storage"""
        conn = self.get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                attributes TEXT,  -- JSON
                source_file TEXT,
                confidence REAL,
                file_size_bytes INTEGER,
                line_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_entity TEXT,
                target_entity TEXT,
                relationship_type TEXT,
                description TEXT,
                confidence REAL,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_entity) REFERENCES entities (id),
                FOREIGN KEY (target_entity) REFERENCES entities (id)
            );
            
            CREATE TABLE IF NOT EXISTS extraction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                content_hash TEXT,
                entities_count INTEGER,
                relationships_count INTEGER,
                confidence REAL,
                processing_time REAL,
                token_usage INTEGER,
                cost_estimate REAL,
                completion_status TEXT,
                summary TEXT,
                file_size_bytes INTEGER,
                line_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS progress_sessions (
                session_id TEXT PRIMARY KEY,
                total_files INTEGER,
                completed_files INTEGER,
                failed_files INTEGER,
                start_time REAL,
                phase TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Enhanced indices for navigation
            CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
            CREATE INDEX IF NOT EXISTS idx_entities_source ON entities(source_file);
            CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
            CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
            CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_file);
            CREATE INDEX IF NOT EXISTS idx_extraction_logs_hash ON extraction_logs(content_hash);
            CREATE INDEX IF NOT EXISTS idx_extraction_logs_path ON extraction_logs(file_path);
        """)
        conn.commit()
        conn.close()
    
    async def store_entities_async(self, entities: List[Dict], session_id: str = None):
        """Store entities asynchronously"""
        def _store_entities(entities_data):
            conn = self.get_connection()
            for entity_data in entities_data:
                conn.execute("""
                    INSERT OR REPLACE INTO entities 
                    (id, name, type, description, attributes, source_file, confidence, file_size_bytes, line_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_data['id'], entity_data['name'], entity_data['type'], 
                    entity_data['description'], json.dumps(entity_data.get('attributes', {})),
                    entity_data['source_file'], entity_data['confidence'],
                    entity_data.get('file_size_bytes', 0), entity_data.get('line_count', 0)
                ))
            conn.commit()
            conn.close()
        
        # Run in thread executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _store_entities, entities)
    
    async def log_extraction_async(self, result: AsyncExtractionResult):
        """Log extraction results asynchronously"""
        def _log_extraction(result_data):
            conn = self.get_connection()
            conn.execute("""
                INSERT INTO extraction_logs
                (file_path, content_hash, entities_count, relationships_count, 
                 confidence, processing_time, token_usage, cost_estimate, 
                 completion_status, summary, file_size_bytes, line_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_data.file_path, result_data.content_hash, len(result_data.entities),
                len(result_data.relationships), result_data.confidence, result_data.processing_time,
                result_data.token_usage, result_data.cost_estimate, result_data.completion_status,
                result_data.summary, result_data.file_size_bytes, result_data.line_count
            ))
            conn.commit()
            conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _log_extraction, result)
    
    async def update_progress_async(self, progress: ProgressState):
        """Update progress state asynchronously"""
        def _update_progress(progress_data):
            conn = self.get_connection()
            conn.execute("""
                INSERT OR REPLACE INTO progress_sessions
                (session_id, total_files, completed_files, failed_files, start_time, phase)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                progress_data.session_id, progress_data.total_files, 
                progress_data.completed_files, progress_data.failed_files,
                progress_data.start_time, progress_data.phase
            ))
            conn.commit()
            conn.close()
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _update_progress, progress)

class AsyncHaikuKnowledgeExtractor:
    """Enhanced async knowledge extraction subagent"""
    
    def __init__(self, 
                 anthropic_api_key: str = None,
                 output_base_dir: str = "/Users/stiglau/utvikling/privat/komposteur/docs/knowledge-analysis",
                 target_codebase: str = "/Users/stiglau/utvikling/privat/komposteur",
                 cost_limit_daily: float = 5.00,
                 enable_caching: bool = True,
                 max_workers: int = None,
                 file_timeout_seconds: int = 30):
        
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None
        
        # Setup paths
        self.output_base_dir = Path(output_base_dir)
        self.target_codebase = Path(target_codebase)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Database in target project directory
        db_path = self.target_codebase / "docs" / "knowledge-analysis" / "knowledge_graph.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = AsyncLightweightGraphDB(str(db_path))
        
        self.cost_limit_daily = cost_limit_daily
        self.enable_caching = enable_caching
        self.daily_cost = 0.0
        self.file_timeout = file_timeout_seconds
        
        # Worker configuration
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        
        # Haiku pricing (as of 2025)
        self.haiku_input_cost = 0.25 / 1_000_000  # $0.25 per 1M input tokens
        self.haiku_output_cost = 1.25 / 1_000_000  # $1.25 per 1M output tokens
        
        # Enhanced file filtering patterns for comprehensive Java/Maven projects
        self.source_file_extensions = {
            # Java/Kotlin ecosystem
            '.java', '.kt', '.kts', '.scala', '.groovy',
            # Web technologies
            '.js', '.ts', '.jsx', '.tsx', '.vue', '.html', '.css', '.scss', '.less',
            # Python ecosystem
            '.py', '.pyx', '.pyi', '.ipynb',
            # Configuration and build files
            '.xml', '.json', '.yml', '.yaml', '.properties', '.conf', '.cfg', '.ini',
            '.gradle', '.maven', '.sbt',
            # Documentation
            '.md', '.rst', '.adoc', '.txt',
            # Shell scripts and tools
            '.sh', '.bat', '.cmd', '.ps1',
            # Other common source files
            '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', '.php', '.rb', '.pl', '.sql'
        }
        
        self.ignored_patterns = {
            # Compiled/Generated files
            '.class', '.jar', '.war', '.ear', '.pyc', '.pyo', '__pycache__',
            '.o', '.so', '.dylib', '.dll', '.exe',
            # Build directories  
            'target/', 'build/', 'dist/', 'out/', 'bin/', 'obj/',
            'node_modules/', '.gradle/', '.maven/', '.m2/',
            # IDE files
            '.idea/', '.vscode/', '.eclipse/', '*.iml', '.settings/',
            '.classpath', '.project',
            # Version control
            '.git/', '.svn/', '.hg/', '.bzr/',
            # Logs and temp
            '*.log', 'logs/', 'tmp/', 'temp/', '.tmp', '*.tmp',
            # System files
            '.DS_Store', 'Thumbs.db', '*.swp', '*.swo',
            # Large media files
            '*.mp4', '*.avi', '*.mov', '*.wmv', '*.flv', '*.webm',
            '*.mp3', '*.wav', '*.flac', '*.ogg', '*.aac',
            '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.svg',
            '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt', '*.pptx'
        }
        
        # Navigation tracking
        self.navigation_index = NavigationIndex(
            classes=defaultdict(list),
            functions=defaultdict(list),
            packages=defaultdict(list),
            technologies=set(),
            file_types=defaultdict(int),
            dependency_graph=defaultdict(list)
        )
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking
        self.current_session = None
    
    def should_process_file(self, file_path: Path) -> bool:
        """Enhanced file filtering with better pattern matching"""
        
        # Check against ignored patterns first
        file_str = str(file_path).lower()
        for pattern in self.ignored_patterns:
            if pattern.endswith('/'):
                if pattern[:-1] in file_str.split(os.sep):
                    return False
            elif pattern in file_str or file_str.endswith(pattern.lstrip('*')):
                return False
        
        # Check if it's a source file extension
        if file_path.suffix.lower() not in self.source_file_extensions:
            return False
        
        # Skip very large files (>5MB for comprehensive scan)
        try:
            file_size = file_path.stat().st_size
            if file_size > 5_000_000:
                self.logger.warning(f"Skipping large file: {file_path} ({file_size / 1_000_000:.1f}MB)")
                return False
            if file_size == 0:
                return False  # Empty files
        except (OSError, IOError):
            return False
        
        return True
    
    def get_file_priority(self, file_path: Path) -> int:
        """Enhanced priority system for comprehensive scanning"""
        extension = file_path.suffix.lower()
        file_name = file_path.name.lower()
        
        # Priority 0: Critical Maven/build files
        if file_name in {'pom.xml', 'build.gradle', 'settings.gradle', 'package.json', 'pyproject.toml'}:
            return 0
        
        # Priority 1: Main Java/Kotlin source files
        if extension in {'.java', '.kt'} and 'src/main' in str(file_path):
            return 1
        
        # Priority 2: Test Java/Kotlin files
        if extension in {'.java', '.kt'} and ('src/test' in str(file_path) or 'test' in str(file_path)):
            return 2
        
        # Priority 3: Configuration files
        if extension in {'.xml', '.yml', '.yaml', '.properties', '.json'} and file_name not in {'package-lock.json'}:
            return 3
        
        # Priority 4: Python/JS/TS source files
        if extension in {'.py', '.js', '.ts', '.tsx'}:
            return 4
        
        # Priority 5: Shell scripts and automation
        if extension in {'.sh', '.bat', '.cmd', '.ps1'} or file_name in {'Makefile', 'makefile', 'Dockerfile'}:
            return 5
        
        # Priority 6: Documentation
        if extension in {'.md', '.rst', '.adoc', '.txt'}:
            return 6
        
        return 7
    
    def read_file_content_safe(self, file_path: Path) -> Tuple[Optional[str], int, int]:
        """Thread-safe file reading with encoding detection and metadata"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                content = file_path.read_text(encoding=encoding)
                file_size = file_path.stat().st_size
                line_count = content.count('\n') + 1 if content else 0
                return content, file_size, line_count
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                self.logger.warning(f"Error reading {file_path}: {e}")
                break
        
        return None, 0, 0
    
    async def extract_knowledge_with_timeout(self, content: str, file_path: str, 
                                           file_size: int, line_count: int) -> AsyncExtractionResult:
        """Extract knowledge with timeout protection"""
        try:
            # Use asyncio.wait_for to enforce timeout
            result = await asyncio.wait_for(
                self.extract_knowledge_haiku(content, file_path, file_size, line_count),
                timeout=self.file_timeout
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout processing {file_path} after {self.file_timeout}s")
            return self.extract_knowledge_heuristic(
                content, file_path, time.time(), file_size, line_count,
                error_info=f"Processing timeout after {self.file_timeout}s"
            )
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return self.extract_knowledge_heuristic(
                content, file_path, time.time(), file_size, line_count, 
                error_info=str(e)
            )
    
    async def extract_knowledge_haiku(self, content: str, file_path: str, 
                                    file_size: int, line_count: int) -> AsyncExtractionResult:
        """Enhanced Haiku-based knowledge extraction"""
        start_time = time.time()
        
        if not self.client:
            return self.extract_knowledge_heuristic(content, file_path, start_time, 
                                                  file_size, line_count)
        
        # Check daily cost limit
        if self.daily_cost >= self.cost_limit_daily:
            self.logger.warning(f"Daily cost limit reached: ${self.daily_cost:.3f}")
            return self.extract_knowledge_heuristic(content, file_path, start_time,
                                                  file_size, line_count)
        
        # Enhanced system prompt for comprehensive extraction
        system_prompt = """You are a comprehensive technical knowledge extraction specialist with expertise in Java, Kotlin, Maven, TypeScript, JavaScript, Python, and software architecture.

🚨 CRITICAL CONSTRAINTS:
- YOU ARE STRICTLY READ-ONLY - NO modification suggestions
- EXTRACT ONLY - analyze code structure and relationships
- FOCUS on architectural patterns, dependencies, and key entities

Extract detailed information about:
1. ENTITIES: Classes, functions, interfaces, annotations, packages, Maven dependencies
2. RELATIONSHIPS: Dependencies, inheritance, implementations, imports, calls
3. SUMMARY: Key architectural patterns and technologies used

ENTITY TYPES (be specific):
- class, abstract_class, interface, enum, annotation
- function, method, constructor
- package, module, namespace
- maven_dependency, gradle_dependency, npm_dependency
- configuration, property, constant
- service, repository, controller, entity, dto
- test, test_class, test_method
- utility, helper, factory, builder
- technology, framework, library
- database, table, schema
- api_endpoint, rest_controller, web_service

RELATIONSHIP TYPES:
- extends, implements, inherits
- imports, depends_on, uses, calls
- contains, composed_of, aggregates
- configures, autowires, injects
- tests, mocks, validates
- overrides, abstracts, delegates

Focus on:
- Maven module structure and dependencies
- Spring framework usage and annotations  
- Package organization and naming patterns
- Test class relationships and coverage
- Configuration and property management
- Database entity relationships
- API endpoint definitions

Handle errors gracefully - if content has parsing issues, extract what you can.

Respond with valid JSON:
{
  "entities": [{"name": "EntityName", "type": "class", "description": "brief description"}],
  "relationships": [{"source": "EntityA", "target": "EntityB", "type": "extends", "description": "relationship"}],
  "summary": "Concise overview of main components and architecture",
  "confidence": 0.85,
  "completion_status": "success"
}"""

        try:
            # Smart truncation for very long files
            if len(content) > 12000:
                lines = content.split('\n')
                if len(lines) > 300:
                    # Take first 200 lines + last 100 lines for context
                    truncated_content = '\n'.join(lines[:200] + ['', '... [TRUNCATED] ...', ''] + lines[-100:])
                else:
                    truncated_content = content[:12000] + "\n... [TRUNCATED]"
            else:
                truncated_content = content
            
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.1,
                system=system_prompt,
                messages=[{
                    "role": "user", 
                    "content": f"File: {file_path} ({file_size} bytes, {line_count} lines)\n\nContent:\n{truncated_content}"
                }]
            )
            
            # Calculate costs more accurately
            input_tokens = len(truncated_content.split()) * 1.3
            output_tokens = len(response.content[0].text.split()) * 1.3
            cost = (input_tokens * self.haiku_input_cost + 
                   output_tokens * self.haiku_output_cost)
            self.daily_cost += cost
            
            # Enhanced JSON parsing with better error handling
            response_text = response.content[0].text.strip()
            
            # Clean up JSON response
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            # Attempt to parse JSON with fallback
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as je:
                self.logger.warning(f"JSON parse error in {file_path}: {je}")
                # Try to extract partial data or fall back to heuristic
                return self.extract_knowledge_heuristic(
                    content, file_path, start_time, file_size, line_count,
                    error_info=f"JSON parse error: {je}"
                )
            
            processing_time = time.time() - start_time
            
            return AsyncExtractionResult(
                file_path=file_path,
                content_hash=self.get_content_hash(content),
                entities=data.get('entities', []),
                relationships=data.get('relationships', []),
                summary=data.get('summary', 'No summary available'),
                confidence=data.get('confidence', 0.0),
                processing_time=processing_time,
                token_usage=int(input_tokens + output_tokens),
                cost_estimate=cost,
                completion_status=data.get('completion_status', 'success'),
                file_size_bytes=file_size,
                line_count=line_count
            )
            
        except Exception as e:
            self.logger.error(f"Haiku extraction failed for {file_path}: {e}")
            return self.extract_knowledge_heuristic(content, file_path, start_time, 
                                                  file_size, line_count, str(e))
    
    def extract_knowledge_heuristic(self, content: str, file_path: str, 
                                  start_time: float, file_size: int, line_count: int,
                                  error_info: str = None) -> AsyncExtractionResult:
        """Enhanced fallback heuristic extraction"""
        entities = []
        relationships = []
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # Java/Kotlin patterns
            if file_ext in {'.java', '.kt'}:
                # Classes
                class_matches = re.findall(r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)', content)
                for class_name in class_matches:
                    entities.append({
                        'name': class_name,
                        'type': 'class',
                        'description': f'Java/Kotlin class in {Path(file_path).name}'
                    })
                
                # Interfaces
                interface_matches = re.findall(r'(?:public\s+)?interface\s+([A-Za-z_][A-Za-z0-9_]*)', content)
                for interface_name in interface_matches:
                    entities.append({
                        'name': interface_name,
                        'type': 'interface',
                        'description': f'Interface in {Path(file_path).name}'
                    })
                
                # Methods
                method_matches = re.findall(r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\{', content)
                for method_name in method_matches[:10]:  # Limit to first 10
                    entities.append({
                        'name': method_name,
                        'type': 'method',
                        'description': f'Method in {Path(file_path).name}'
                    })
                
                # Annotations
                annotation_matches = re.findall(r'@([A-Za-z_][A-Za-z0-9_]*)', content)
                for annotation in set(annotation_matches):
                    entities.append({
                        'name': annotation,
                        'type': 'annotation',
                        'description': f'Annotation used in {Path(file_path).name}'
                    })
            
            # Python patterns
            elif file_ext == '.py':
                class_matches = re.findall(r'class\s+([A-Za-z_][A-Za-z0-9_]*)', content)
                for class_name in class_matches:
                    entities.append({
                        'name': class_name,
                        'type': 'class',
                        'description': f'Python class in {Path(file_path).name}'
                    })
                
                func_matches = re.findall(r'def\s+([A-Za-z_][A-Za-z0-9_]*)', content)
                for func_name in func_matches[:15]:  # Limit functions
                    entities.append({
                        'name': func_name,
                        'type': 'function',
                        'description': f'Python function in {Path(file_path).name}'
                    })
            
            # Maven pom.xml patterns
            elif file_path.endswith('pom.xml'):
                # Dependencies
                dep_matches = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
                for artifact in set(dep_matches[:20]):  # Limit dependencies
                    entities.append({
                        'name': artifact,
                        'type': 'maven_dependency',
                        'description': f'Maven dependency in {Path(file_path).name}'
                    })
            
            # Technology detection
            tech_patterns = {
                r'\bspring\b': 'Spring Framework',
                r'\bhibernate\b': 'Hibernate ORM',
                r'\bjunit\b': 'JUnit Testing',
                r'\bmockito\b': 'Mockito',
                r'\baws\b': 'AWS',
                r'\bdocker\b': 'Docker',
                r'\bkubernetes\b': 'Kubernetes',
                r'\breact\b': 'React',
                r'\bangular\b': 'Angular',
                r'\bvue\b': 'Vue.js'
            }
            
            content_lower = content.lower()
            for pattern, tech_name in tech_patterns.items():
                if re.search(pattern, content_lower):
                    entities.append({
                        'name': tech_name,
                        'type': 'technology',
                        'description': f'Technology detected in {Path(file_path).name}'
                    })
            
            # Generate summary
            summary = f"Heuristic analysis of {Path(file_path).name}: {len(entities)} entities extracted from {line_count} lines"
            
        except Exception as e:
            self.logger.warning(f"Heuristic extraction error for {file_path}: {e}")
            summary = f"Error during heuristic extraction: {e}"
        
        processing_time = time.time() - start_time
        
        return AsyncExtractionResult(
            file_path=file_path,
            content_hash=self.get_content_hash(content),
            entities=entities,
            relationships=relationships,
            summary=summary,
            confidence=0.5 if not error_info else 0.2,
            processing_time=processing_time,
            token_usage=0,
            cost_estimate=0.0,
            completion_status='heuristic_fallback' if not error_info else 'failed',
            error_info=error_info,
            file_size_bytes=file_size,
            line_count=line_count
        )
    
    def get_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def process_single_file(self, file_path: Path) -> Optional[AsyncExtractionResult]:
        """Process a single file with full error protection"""
        if not self.should_process_file(file_path):
            return None
        
        try:
            content, file_size, line_count = self.read_file_content_safe(file_path)
            if not content:
                return None
            
            # Check cache
            content_hash = self.get_content_hash(content)
            if self.enable_caching:
                conn = self.db.get_connection()
                cursor = conn.execute(
                    "SELECT * FROM extraction_logs WHERE content_hash = ? ORDER BY created_at DESC LIMIT 1",
                    (content_hash,)
                )
                cached = cursor.fetchone()
                conn.close()
                if cached:
                    self.logger.debug(f"Using cached extraction for {file_path}")
                    return None  # Already processed
            
            # Process with timeout protection
            result = await self.extract_knowledge_with_timeout(
                content, str(file_path), file_size, line_count
            )
            
            # Update navigation index
            self.update_navigation_index(result, file_path)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process {file_path}: {e}")
            return None
    
    def update_navigation_index(self, result: AsyncExtractionResult, file_path: Path):
        """Update navigation index with extracted information"""
        try:
            file_str = str(file_path)
            
            # Update file type count
            self.navigation_index.file_types[file_path.suffix] += 1
            
            # Update entity-based indices
            for entity in result.entities:
                entity_type = entity.get('type', 'unknown')
                entity_name = entity.get('name', 'unknown')
                
                if entity_type == 'class':
                    self.navigation_index.classes[entity_name].append(file_str)
                elif entity_type in {'function', 'method'}:
                    self.navigation_index.functions[entity_name].append(file_str)
                elif entity_type == 'package':
                    self.navigation_index.packages[entity_name].append(file_str)
                elif entity_type == 'technology':
                    self.navigation_index.technologies.add(entity_name)
            
        except Exception as e:
            self.logger.warning(f"Failed to update navigation index for {file_path}: {e}")
    
    async def scan_directory_comprehensive(self, 
                                         directory: Path = None,
                                         session_id: str = None) -> List[AsyncExtractionResult]:
        """Comprehensive directory scanning with progress tracking"""
        
        if directory is None:
            directory = self.target_codebase
            
        if session_id is None:
            session_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"🚀 Starting comprehensive scan of {directory}")
        self.logger.info(f"📊 Session ID: {session_id}")
        
        # Initialize progress tracking
        progress = ProgressState(
            session_id=session_id,
            total_files=0,
            completed_files=0,
            failed_files=0,
            start_time=time.time(),
            phase="scanning"
        )
        
        # Phase 1: File Discovery
        self.logger.info("📂 Phase 1: Discovering files...")
        all_files = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and self.should_process_file(file_path):
                priority = self.get_file_priority(file_path)
                all_files.append((priority, file_path))
        
        # Sort by priority (lower number = higher priority)
        all_files.sort(key=lambda x: (x[0], str(x[1])))
        
        progress.total_files = len(all_files)
        progress.phase = "processing"
        await self.db.update_progress_async(progress)
        
        self.logger.info(f"📋 Found {progress.total_files} files to process")
        self.logger.info(f"👥 Using {self.max_workers} workers for parallel processing")
        
        # Phase 2: Parallel Processing
        results = []
        completed_files = 0
        failed_files = 0
        
        # Process files in batches to manage memory
        batch_size = min(100, self.max_workers * 4)
        
        for i in range(0, len(all_files), batch_size):
            batch = all_files[i:i + batch_size]
            self.logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(all_files) + batch_size - 1)//batch_size}")
            
            # Create tasks for this batch
            tasks = []
            for priority, file_path in batch:
                task = asyncio.create_task(
                    self.process_single_file(file_path),
                    name=str(file_path)
                )
                tasks.append(task)
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process batch results
            for j, result in enumerate(batch_results):
                priority, file_path = batch[j]
                
                if isinstance(result, Exception):
                    self.logger.error(f"❌ Failed to process {file_path}: {result}")
                    failed_files += 1
                elif result is not None:
                    results.append(result)
                    completed_files += 1
                    
                    # Store in database
                    try:
                        await self.db.log_extraction_async(result)
                    except Exception as e:
                        self.logger.warning(f"Failed to log extraction for {file_path}: {e}")
                else:
                    completed_files += 1  # Cached or skipped
            
            # Update progress
            progress.completed_files = completed_files
            progress.failed_files = failed_files
            progress.current_file = str(batch[-1][1]) if batch else None
            await self.db.update_progress_async(progress)
            
            # Progress logging
            if completed_files % 50 == 0 or completed_files == progress.total_files:
                elapsed = time.time() - progress.start_time
                rate = completed_files / elapsed if elapsed > 0 else 0
                remaining = progress.total_files - completed_files
                eta = remaining / rate if rate > 0 else 0
                
                self.logger.info(f"📈 Progress: {completed_files}/{progress.total_files} "
                               f"({completed_files/progress.total_files*100:.1f}%) "
                               f"Rate: {rate:.1f} files/sec "
                               f"ETA: {eta/60:.1f}min")
        
        # Final progress update
        progress.phase = "completed"
        progress.completed_files = completed_files
        progress.failed_files = failed_files
        await self.db.update_progress_async(progress)
        
        total_time = time.time() - progress.start_time
        self.logger.info(f"✅ Scan completed in {total_time/60:.1f} minutes")
        self.logger.info(f"📊 Results: {len(results)} successful, {failed_files} failed")
        
        return results
    
    async def generate_comprehensive_reports(self, results: List[AsyncExtractionResult], 
                                           session_id: str) -> Dict[str, Path]:
        """Generate comprehensive reporting suite"""
        
        self.logger.info("📝 Generating comprehensive reports...")
        
        # Create session directory
        session_dir = self.output_base_dir / f"session_{session_id}"
        session_dir.mkdir(exist_ok=True)
        
        report_files = {}
        
        # 1. Main extraction report
        main_report = self.generate_main_report(results, session_id)
        main_report_file = session_dir / "extraction_report.md"
        main_report_file.write_text(main_report)
        report_files['main_report'] = main_report_file
        
        # 2. Navigation index
        nav_index = self.generate_navigation_index()
        nav_index_file = session_dir / "navigation_index.md"
        nav_index_file.write_text(nav_index)
        report_files['navigation_index'] = nav_index_file
        
        # 3. Function/Class directory
        func_class_dir = self.generate_function_class_directory(results)
        func_class_file = session_dir / "function_class_directory.md"
        func_class_file.write_text(func_class_dir)
        report_files['function_class_directory'] = func_class_file
        
        # 4. Package organization overview
        package_overview = self.generate_package_overview(results)
        package_file = session_dir / "package_organization.md"
        package_file.write_text(package_overview)
        report_files['package_overview'] = package_file
        
        # 5. Maven dependency mapping
        maven_deps = self.generate_maven_dependency_mapping(results)
        maven_file = session_dir / "maven_dependencies.md"
        maven_file.write_text(maven_deps)
        report_files['maven_dependencies'] = maven_file
        
        # 6. Technology stack summary
        tech_stack = self.generate_technology_stack_summary(results)
        tech_file = session_dir / "technology_stack.md"
        tech_file.write_text(tech_stack)
        report_files['technology_stack'] = tech_file
        
        # 7. Database export (JSON format for LLM consumption)
        db_export = await self.export_database_json()
        db_export_file = session_dir / "knowledge_database.json"
        db_export_file.write_text(json.dumps(db_export, indent=2))
        report_files['database_export'] = db_export_file
        
        # 8. Master index file
        master_index = self.generate_master_index(report_files, session_id)
        master_index_file = session_dir / "README.md"
        master_index_file.write_text(master_index)
        report_files['master_index'] = master_index_file
        
        self.logger.info(f"📚 Generated {len(report_files)} comprehensive reports in {session_dir}")
        return report_files
    
    def generate_main_report(self, results: List[AsyncExtractionResult], session_id: str) -> str:
        """Generate main extraction report"""
        timestamp = datetime.now().isoformat()
        
        # Statistics
        total_files = len(results)
        total_entities = sum(len(r.entities) for r in results)
        total_relationships = sum(len(r.relationships) for r in results)
        total_lines = sum(r.line_count for r in results)
        total_size_mb = sum(r.file_size_bytes for r in results) / 1_000_000
        avg_confidence = sum(r.confidence for r in results) / total_files if total_files > 0 else 0
        total_cost = sum(r.cost_estimate for r in results)
        
        # Status distribution
        status_counts = defaultdict(int)
        for result in results:
            status_counts[result.completion_status] += 1
        
        # File type distribution
        file_types = defaultdict(int)
        for result in results:
            ext = Path(result.file_path).suffix
            file_types[ext] += 1
        
        return f"""# Comprehensive Knowledge Extraction Report

**Session ID**: `{session_id}`
**Generated**: {timestamp}
**Codebase**: {self.target_codebase}
**Extraction Agent**: Enhanced Async Knowledge Extractor v2.0

## 📊 Executive Summary

- **Files Analyzed**: {total_files:,}
- **Total Lines of Code**: {total_lines:,}
- **Total File Size**: {total_size_mb:.1f} MB
- **Entities Extracted**: {total_entities:,}
- **Relationships Mapped**: {total_relationships:,}
- **Average Confidence**: {avg_confidence:.1%}
- **Total Processing Cost**: ${total_cost:.4f}

## 📈 Processing Results

### Status Distribution
{chr(10).join(f"- **{status}**: {count} files" for status, count in status_counts.items())}

### File Type Coverage
{chr(10).join(f"- **{ext or 'no extension'}**: {count} files" for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10])}

## 🏗️ Architecture Overview

### Entity Distribution
{self._generate_entity_distribution(results)}

### Technology Stack Detected
{chr(10).join(f"- {tech}" for tech in sorted(self.navigation_index.technologies))}

## 📂 Codebase Structure

### Top Packages by File Count
{self._generate_top_packages()}

### Largest Files Analyzed
{self._generate_largest_files(results)}

## 🎯 Quality Metrics

**Extraction Quality**: {"🟢 Excellent" if avg_confidence >= 0.8 else "🟡 Good" if avg_confidence >= 0.6 else "🔴 Needs Review"}

**Coverage**: {(status_counts.get('success', 0) / total_files * 100 if total_files > 0 else 0):.1f}% successful extractions

**Processing Efficiency**: {(total_files / (sum(r.processing_time for r in results) / 60) if sum(r.processing_time for r in results) > 0 else 0):.1f} files/minute

## 📋 Navigation Guide

1. **[Navigation Index](navigation_index.md)** - Quick file and component lookup
2. **[Function/Class Directory](function_class_directory.md)** - Complete entity catalog
3. **[Package Organization](package_organization.md)** - Module structure overview
4. **[Maven Dependencies](maven_dependencies.md)** - Dependency mapping
5. **[Technology Stack](technology_stack.md)** - Detailed technology analysis
6. **[Database Export](knowledge_database.json)** - Raw data for LLM consumption

---
*Generated by Enhanced Async Knowledge Extractor - Comprehensive Codebase Analysis*
"""
    
    def _generate_entity_distribution(self, results: List[AsyncExtractionResult]) -> str:
        """Generate entity distribution summary"""
        entity_counts = defaultdict(int)
        for result in results:
            for entity in result.entities:
                entity_counts[entity.get('type', 'unknown')] += 1
        
        lines = []
        for entity_type, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            lines.append(f"- **{entity_type}**: {count}")
        
        return '\n'.join(lines)
    
    def _generate_top_packages(self) -> str:
        """Generate top packages by file count"""
        package_counts = [(pkg, len(files)) for pkg, files in self.navigation_index.packages.items()]
        package_counts.sort(key=lambda x: x[1], reverse=True)
        
        lines = []
        for pkg, count in package_counts[:10]:
            lines.append(f"- **{pkg}**: {count} files")
        
        return '\n'.join(lines) if lines else "- No packages detected"
    
    def _generate_largest_files(self, results: List[AsyncExtractionResult]) -> str:
        """Generate largest files summary"""
        sorted_results = sorted(results, key=lambda x: x.file_size_bytes, reverse=True)
        
        lines = []
        for result in sorted_results[:10]:
            size_kb = result.file_size_bytes / 1000
            lines.append(f"- **{Path(result.file_path).name}** ({size_kb:.1f}KB, {result.line_count} lines)")
        
        return '\n'.join(lines)
    
    def generate_navigation_index(self) -> str:
        """Generate navigation index for easy lookup"""
        return f"""# Navigation Index

Quick lookup guide for navigating the codebase.

## 🏛️ Classes ({len(self.navigation_index.classes)})

{self._format_navigation_section(dict(self.navigation_index.classes))}

## 🔧 Functions/Methods ({len(self.navigation_index.functions)})

{self._format_navigation_section(dict(self.navigation_index.functions), limit=50)}

## 📦 Packages ({len(self.navigation_index.packages)})

{self._format_navigation_section(dict(self.navigation_index.packages))}

## 🛠️ Technologies Detected

{chr(10).join(f"- {tech}" for tech in sorted(self.navigation_index.technologies))}

## 📊 File Types

{chr(10).join(f"- **{ext}**: {count} files" for ext, count in sorted(self.navigation_index.file_types.items(), key=lambda x: x[1], reverse=True))}

---
*Use Ctrl+F to quickly find specific classes, functions, or packages*
"""
    
    def _format_navigation_section(self, items_dict: Dict[str, List[str]], limit: int = None) -> str:
        """Format a navigation section with optional limit"""
        if not items_dict:
            return "- None detected"
        
        lines = []
        sorted_items = sorted(items_dict.items())
        
        if limit and len(sorted_items) > limit:
            sorted_items = sorted_items[:limit]
            lines.append(f"*Showing top {limit} of {len(items_dict)} total*\n")
        
        for name, files in sorted_items:
            if len(files) == 1:
                lines.append(f"- **{name}** → `{files[0]}`")
            else:
                lines.append(f"- **{name}** → {len(files)} files")
                for file_path in files[:3]:  # Show first 3 files
                    lines.append(f"  - `{file_path}`")
                if len(files) > 3:
                    lines.append(f"  - ... and {len(files) - 3} more")
        
        return '\n'.join(lines)
    
    def generate_function_class_directory(self, results: List[AsyncExtractionResult]) -> str:
        """Generate comprehensive function and class directory"""
        entities_by_type = defaultdict(list)
        
        for result in results:
            for entity in result.entities:
                entities_by_type[entity.get('type', 'unknown')].append({
                    'name': entity.get('name'),
                    'description': entity.get('description'),
                    'file': result.file_path
                })
        
        content = "# Function & Class Directory\n\n"
        content += "Comprehensive listing of all extracted entities.\n\n"
        
        for entity_type in sorted(entities_by_type.keys()):
            entities = entities_by_type[entity_type]
            content += f"## {entity_type.replace('_', ' ').title()} ({len(entities)})\n\n"
            
            # Sort by name
            entities.sort(key=lambda x: x['name'])
            
            for entity in entities:
                content += f"### {entity['name']}\n"
                content += f"- **File**: `{entity['file']}`\n"
                content += f"- **Description**: {entity['description']}\n\n"
        
        return content
    
    def generate_package_overview(self, results: List[AsyncExtractionResult]) -> str:
        """Generate package organization overview"""
        # Analyze package structure from file paths
        packages = defaultdict(lambda: {'files': [], 'entities': [], 'technologies': set()})
        
        for result in results:
            # Extract package from file path
            path_parts = Path(result.file_path).parts
            
            # Find package structure
            if 'src/main/java' in str(result.file_path):
                # Maven Java structure
                try:
                    java_idx = path_parts.index('java')
                    if java_idx + 1 < len(path_parts):
                        package_path = '.'.join(path_parts[java_idx + 1:-1])
                        if package_path:
                            packages[package_path]['files'].append(result.file_path)
                            packages[package_path]['entities'].extend(result.entities)
                except ValueError:
                    pass
            
            # Also categorize by directory structure
            if len(path_parts) > 2:
                parent_dir = '/'.join(path_parts[-3:-1])  # Last 2 directories
                packages[parent_dir]['files'].append(result.file_path)
        
        content = "# Package Organization Overview\n\n"
        content += "Analysis of the codebase package and directory structure.\n\n"
        
        # Sort packages by file count
        sorted_packages = sorted(packages.items(), key=lambda x: len(x[1]['files']), reverse=True)
        
        content += "## Package Summary\n\n"
        content += "| Package | Files | Description |\n"
        content += "|---------|-------|-------------|\n"
        
        for package, data in sorted_packages[:20]:  # Top 20 packages
            file_count = len(data['files'])
            # Infer package purpose from name
            purpose = self._infer_package_purpose(package)
            content += f"| `{package}` | {file_count} | {purpose} |\n"
        
        content += "\n## Detailed Package Analysis\n\n"
        
        for package, data in sorted_packages[:10]:  # Detailed view for top 10
            content += f"### {package}\n\n"
            content += f"- **Files**: {len(data['files'])}\n"
            content += f"- **Sample Files**:\n"
            
            for file_path in data['files'][:5]:  # Show first 5 files
                content += f"  - `{Path(file_path).name}`\n"
            
            if len(data['files']) > 5:
                content += f"  - ... and {len(data['files']) - 5} more\n"
            
            content += "\n"
        
        return content
    
    def _infer_package_purpose(self, package: str) -> str:
        """Infer package purpose from name"""
        package_lower = package.lower()
        
        if 'controller' in package_lower or 'rest' in package_lower:
            return "REST controllers and web endpoints"
        elif 'service' in package_lower:
            return "Business logic services"
        elif 'repository' in package_lower or 'dao' in package_lower:
            return "Data access layer"
        elif 'model' in package_lower or 'entity' in package_lower:
            return "Data models and entities"
        elif 'dto' in package_lower or 'vo' in package_lower:
            return "Data transfer objects"
        elif 'util' in package_lower or 'helper' in package_lower:
            return "Utility classes and helpers"
        elif 'config' in package_lower:
            return "Configuration classes"
        elif 'test' in package_lower:
            return "Test classes"
        elif 'main' in package_lower:
            return "Main application code"
        else:
            return "General package"
    
    def generate_maven_dependency_mapping(self, results: List[AsyncExtractionResult]) -> str:
        """Generate Maven dependency analysis"""
        dependencies = defaultdict(list)
        pom_files = []
        
        for result in results:
            if result.file_path.endswith('pom.xml'):
                pom_files.append(result.file_path)
                
                for entity in result.entities:
                    if entity.get('type') == 'maven_dependency':
                        dependencies[entity['name']].append(result.file_path)
        
        content = "# Maven Dependency Mapping\n\n"
        content += f"Analysis of Maven dependencies across {len(pom_files)} POM files.\n\n"
        
        if not dependencies:
            content += "No Maven dependencies detected.\n"
            return content
        
        content += "## Dependency Usage Summary\n\n"
        content += "| Dependency | Usage Count | POM Files |\n"
        content += "|------------|-------------|----------|\n"
        
        # Sort by usage frequency
        sorted_deps = sorted(dependencies.items(), key=lambda x: len(x[1]), reverse=True)
        
        for dep_name, pom_list in sorted_deps:
            usage_count = len(pom_list)
            pom_names = [Path(pom).parent.name for pom in pom_list[:3]]
            pom_display = ', '.join(pom_names)
            if len(pom_list) > 3:
                pom_display += f" (+{len(pom_list) - 3} more)"
            
            content += f"| `{dep_name}` | {usage_count} | {pom_display} |\n"
        
        content += "\n## POM File Analysis\n\n"
        
        for pom_file in pom_files:
            pom_name = Path(pom_file).parent.name
            content += f"### {pom_name}\n"
            content += f"- **File**: `{pom_file}`\n"
            
            # Find dependencies for this POM
            pom_deps = [dep for dep, poms in dependencies.items() if pom_file in poms]
            if pom_deps:
                content += f"- **Dependencies ({len(pom_deps)})**:\n"
                for dep in sorted(pom_deps)[:10]:  # Show first 10
                    content += f"  - `{dep}`\n"
                if len(pom_deps) > 10:
                    content += f"  - ... and {len(pom_deps) - 10} more\n"
            else:
                content += "- **Dependencies**: None detected\n"
            
            content += "\n"
        
        return content
    
    def generate_technology_stack_summary(self, results: List[AsyncExtractionResult]) -> str:
        """Generate detailed technology stack analysis"""
        tech_files = defaultdict(list)
        tech_contexts = defaultdict(set)
        
        for result in results:
            for entity in result.entities:
                if entity.get('type') == 'technology':
                    tech_name = entity['name']
                    tech_files[tech_name].append(result.file_path)
                    
                    # Analyze context
                    file_ext = Path(result.file_path).suffix
                    if file_ext in {'.java', '.kt'}:
                        tech_contexts[tech_name].add('Java/Kotlin')
                    elif file_ext == '.py':
                        tech_contexts[tech_name].add('Python')
                    elif file_ext in {'.js', '.ts'}:
                        tech_contexts[tech_name].add('JavaScript/TypeScript')
                    elif file_ext in {'.xml', '.yml', '.yaml'}:
                        tech_contexts[tech_name].add('Configuration')
        
        content = "# Technology Stack Summary\n\n"
        content += f"Comprehensive analysis of technologies detected across {len(results)} files.\n\n"
        
        if not tech_files:
            content += "No specific technologies detected.\n"
            return content
        
        content += "## Technology Overview\n\n"
        content += "| Technology | File Count | Contexts | Primary Usage |\n"
        content += "|------------|------------|----------|---------------|\n"
        
        sorted_techs = sorted(tech_files.items(), key=lambda x: len(x[1]), reverse=True)
        
        for tech_name, files in sorted_techs:
            file_count = len(files)
            contexts = ', '.join(sorted(tech_contexts[tech_name])) if tech_name in tech_contexts else 'Unknown'
            primary_usage = self._analyze_tech_usage(tech_name, files)
            
            content += f"| **{tech_name}** | {file_count} | {contexts} | {primary_usage} |\n"
        
        content += "\n## Detailed Technology Analysis\n\n"
        
        for tech_name, files in sorted_techs[:10]:  # Top 10 technologies
            content += f"### {tech_name}\n\n"
            content += f"- **Usage**: Found in {len(files)} files\n"
            content += f"- **Contexts**: {', '.join(sorted(tech_contexts[tech_name]))}\n"
            content += f"- **Sample Files**:\n"
            
            for file_path in files[:5]:
                content += f"  - `{Path(file_path).name}` ({Path(file_path).parent.name})\n"
            
            if len(files) > 5:
                content += f"  - ... and {len(files) - 5} more\n"
            
            content += "\n"
        
        return content
    
    def _analyze_tech_usage(self, tech_name: str, files: List[str]) -> str:
        """Analyze primary usage context for a technology"""
        tech_lower = tech_name.lower()
        
        # Count file types
        java_files = sum(1 for f in files if f.endswith(('.java', '.kt')))
        config_files = sum(1 for f in files if f.endswith(('.xml', '.yml', '.yaml', '.properties')))
        test_files = sum(1 for f in files if 'test' in f.lower())
        
        if test_files > len(files) * 0.5:
            return "Testing framework"
        elif java_files > len(files) * 0.7:
            return "Core application framework"
        elif config_files > len(files) * 0.7:
            return "Configuration and setup"
        elif 'spring' in tech_lower:
            return "Enterprise Java framework"
        elif 'aws' in tech_lower:
            return "Cloud services"
        elif tech_lower in {'docker', 'kubernetes'}:
            return "Containerization/orchestration"
        else:
            return "General usage"
    
    def generate_master_index(self, report_files: Dict[str, Path], session_id: str) -> str:
        """Generate master index file"""
        timestamp = datetime.now().isoformat()
        
        content = f"""# Knowledge Extraction Session: {session_id}

**Generated**: {timestamp}
**Target Codebase**: {self.target_codebase}
**Tool**: Enhanced Async Knowledge Extractor v2.0

## 📚 Available Reports

### Core Analysis
- **[Extraction Report](extraction_report.md)** - Main analysis results and statistics
- **[Navigation Index](navigation_index.md)** - Quick lookup for classes, functions, and packages
- **[Function & Class Directory](function_class_directory.md)** - Comprehensive entity catalog

### Structural Analysis  
- **[Package Organization](package_organization.md)** - Module and package structure
- **[Maven Dependencies](maven_dependencies.md)** - Dependency mapping and analysis
- **[Technology Stack](technology_stack.md)** - Detected technologies and frameworks

### Data Export
- **[Knowledge Database](knowledge_database.json)** - Complete data export for LLM consumption

## 🚀 Quick Start

For LLM agents working with this codebase:

1. **Start with Navigation Index** to quickly locate specific components
2. **Review Package Organization** to understand architectural structure  
3. **Check Technology Stack** to understand the technical landscape
4. **Use Knowledge Database JSON** for programmatic access to all extracted data

## 📊 Session Statistics

{self._generate_session_stats()}

## 🔍 Search Tips

- Use your browser's search (Ctrl+F) to find specific terms across reports
- Navigation Index provides the fastest lookup for classes and functions
- Package Organization shows the high-level structure
- Technology Stack reveals the technical dependencies

---
*This knowledge base provides comprehensive insight into the codebase structure, dependencies, and architectural patterns for enhanced development and maintenance.*
"""
        return content
    
    def _generate_session_stats(self) -> str:
        """Generate session statistics for master index"""
        # Get basic stats from database
        try:
            conn = self.db.get_connection()
            
            # File count
            cursor = conn.execute("SELECT COUNT(*) FROM extraction_logs")
            file_count = cursor.fetchone()[0]
            
            # Entity count
            cursor = conn.execute("SELECT COUNT(*) FROM entities")
            entity_count = cursor.fetchone()[0]
            
            # Relationship count
            cursor = conn.execute("SELECT COUNT(*) FROM relationships")
            relationship_count = cursor.fetchone()[0]
            
            conn.close()
            
            return f"""- **Files Analyzed**: {file_count:,}
- **Entities Extracted**: {entity_count:,}
- **Relationships Mapped**: {relationship_count:,}
- **Technologies Detected**: {len(self.navigation_index.technologies)}
- **File Types**: {len(self.navigation_index.file_types)}"""
        
        except Exception as e:
            return f"Statistics unavailable: {e}"
    
    async def export_database_json(self) -> Dict:
        """Export complete database to JSON for LLM consumption"""
        try:
            conn = self.db.get_connection()
            
            # Export entities
            cursor = conn.execute("SELECT * FROM entities")
            entities_columns = [desc[0] for desc in cursor.description]
            entities = [dict(zip(entities_columns, row)) for row in cursor.fetchall()]
            
            # Export relationships
            cursor = conn.execute("SELECT * FROM relationships") 
            relationships_columns = [desc[0] for desc in cursor.description]
            relationships = [dict(zip(relationships_columns, row)) for row in cursor.fetchall()]
            
            # Export extraction logs
            cursor = conn.execute("SELECT * FROM extraction_logs ORDER BY created_at DESC")
            logs_columns = [desc[0] for desc in cursor.description]
            extraction_logs = [dict(zip(logs_columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'export_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'codebase': str(self.target_codebase),
                    'total_entities': len(entities),
                    'total_relationships': len(relationships),
                    'total_files': len(extraction_logs)
                },
                'entities': entities,
                'relationships': relationships,
                'extraction_logs': extraction_logs,
                'navigation_index': {
                    'classes': dict(self.navigation_index.classes),
                    'functions': dict(self.navigation_index.functions), 
                    'packages': dict(self.navigation_index.packages),
                    'technologies': list(self.navigation_index.technologies),
                    'file_types': dict(self.navigation_index.file_types)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export database: {e}")
            return {'error': str(e)}
    
    async def resume_session(self, session_id: str) -> Optional[ProgressState]:
        """Resume a previous extraction session"""
        try:
            conn = self.db.get_connection()
            cursor = conn.execute(
                "SELECT * FROM progress_sessions WHERE session_id = ? ORDER BY updated_at DESC LIMIT 1",
                (session_id,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ProgressState(
                    session_id=row[0],
                    total_files=row[1],
                    completed_files=row[2], 
                    failed_files=row[3],
                    start_time=row[4],
                    phase=row[5]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to resume session {session_id}: {e}")
            return None

# CLI Interface and Background Runner
async def run_comprehensive_extraction(
    target_codebase: str = "/Users/stiglau/utvikling/privat/komposteur",
    output_dir: str = "/Users/stiglau/utvikling/privat/komposteur/docs/knowledge-analysis",
    anthropic_api_key: str = None,
    session_id: str = None,
    resume: bool = False
) -> str:
    """Run comprehensive knowledge extraction"""
    
    extractor = AsyncHaikuKnowledgeExtractor(
        anthropic_api_key=anthropic_api_key,
        output_base_dir=output_dir,
        target_codebase=target_codebase,
        cost_limit_daily=10.00,  # Higher limit for comprehensive scan
        max_workers=16  # Moderate parallelism
    )
    
    # Resume existing session if requested
    if resume and session_id:
        progress = await extractor.resume_session(session_id)
        if progress:
            extractor.logger.info(f"🔄 Resuming session {session_id}")
            extractor.logger.info(f"📊 Progress: {progress.completed_files}/{progress.total_files}")
    
    # Run comprehensive scan
    results = await extractor.scan_directory_comprehensive(session_id=session_id)
    
    # Generate comprehensive reports
    if results:
        final_session_id = session_id or f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_files = await extractor.generate_comprehensive_reports(results, final_session_id)
        
        extractor.logger.info("🎉 Comprehensive knowledge extraction completed!")
        extractor.logger.info(f"📊 Final Results:")
        extractor.logger.info(f"   - Files: {len(results)}")
        extractor.logger.info(f"   - Entities: {sum(len(r.entities) for r in results)}")
        extractor.logger.info(f"   - Cost: ${sum(r.cost_estimate for r in results):.4f}")
        extractor.logger.info(f"📚 Reports: {report_files['master_index']}")
        
        return str(report_files['master_index'])
    
    else:
        extractor.logger.error("❌ No files were successfully processed")
        return ""

# Standalone script runner
async def main():
    """CLI interface for comprehensive extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Async Knowledge Extractor")
    parser.add_argument("--codebase", 
                       default="/Users/stiglau/utvikling/privat/komposteur",
                       help="Target codebase directory")
    parser.add_argument("--output", 
                       default="/Users/stiglau/utvikling/privat/komposteur/docs/knowledge-analysis",
                       help="Output directory")
    parser.add_argument("--api-key", help="Anthropic API key")
    parser.add_argument("--session-id", help="Session ID for tracking")
    parser.add_argument("--resume", action="store_true", help="Resume previous session")
    parser.add_argument("--background", action="store_true", help="Run in background mode")
    
    args = parser.parse_args()
    
    if args.background:
        print("🚀 Starting background knowledge extraction...")
        print(f"📂 Target: {args.codebase}")
        print(f"📝 Output: {args.output}")
        print("🔄 This will run in the background - you can continue other work")
    
    try:
        master_index_file = await run_comprehensive_extraction(
            target_codebase=args.codebase,
            output_dir=args.output,
            anthropic_api_key=args.api_key,
            session_id=args.session_id,
            resume=args.resume
        )
        
        if master_index_file:
            print(f"\n✅ Knowledge extraction completed successfully!")
            print(f"📚 Master index: {master_index_file}")
            print(f"🔍 Open the master index to explore the comprehensive knowledge base")
        else:
            print("\n❌ Knowledge extraction failed")
            
    except KeyboardInterrupt:
        print("\n⏸️ Extraction interrupted by user")
    except Exception as e:
        print(f"\n❌ Extraction failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())