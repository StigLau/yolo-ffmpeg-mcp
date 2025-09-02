#!/usr/bin/env python3
"""
Haiku-Powered Knowledge Extraction Subagent
Scans files/folders, structures data, and builds lightweight graph database
"""

import json
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import logging
import asyncio
import os
import re
from datetime import datetime

# Optional imports with fallbacks
try:
    import networkx as nx
except ImportError:
    # Create dummy nx module for type hints
    class _DummyNX:
        Graph = None
    nx = _DummyNX()

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

@dataclass
class ExtractionResult:
    """Results from knowledge extraction"""
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

@dataclass
class KnowledgeEntity:
    """Extracted knowledge entity"""
    id: str
    name: str
    type: str
    description: str
    attributes: Dict[str, str]
    source_file: str
    confidence: float

@dataclass  
class KnowledgeRelationship:
    """Relationship between entities"""
    id: str
    source_entity: str
    target_entity: str
    relationship_type: str
    description: str
    confidence: float
    source_file: str

class LightweightGraphDB:
    """SQLite-based lightweight graph database"""
    
    def __init__(self, db_path: str = "knowledge_graph.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.setup_schema()
    
    def setup_schema(self):
        """Create database schema for graph storage"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                attributes TEXT,  -- JSON
                source_file TEXT,
                confidence REAL,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
            CREATE INDEX IF NOT EXISTS idx_entities_source ON entities(source_file);
            CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
            CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_file);
            CREATE INDEX IF NOT EXISTS idx_extraction_logs_hash ON extraction_logs(content_hash);
        """)
        self.conn.commit()
    
    def store_entities(self, entities: List[KnowledgeEntity]):
        """Store entities in database"""
        for entity in entities:
            self.conn.execute("""
                INSERT OR REPLACE INTO entities 
                (id, name, type, description, attributes, source_file, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.id, entity.name, entity.type, entity.description,
                json.dumps(entity.attributes), entity.source_file, entity.confidence
            ))
        self.conn.commit()
    
    def store_relationships(self, relationships: List[KnowledgeRelationship]):
        """Store relationships in database"""
        for rel in relationships:
            self.conn.execute("""
                INSERT OR REPLACE INTO relationships
                (id, source_entity, target_entity, relationship_type, description, confidence, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rel.id, rel.source_entity, rel.target_entity, rel.relationship_type,
                rel.description, rel.confidence, rel.source_file
            ))
        self.conn.commit()
    
    def log_extraction(self, result: ExtractionResult):
        """Log extraction results"""
        self.conn.execute("""
            INSERT INTO extraction_logs
            (file_path, content_hash, entities_count, relationships_count, 
             confidence, processing_time, token_usage, cost_estimate, 
             completion_status, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.file_path, result.content_hash, len(result.entities),
            len(result.relationships), result.confidence, result.processing_time,
            result.token_usage, result.cost_estimate, result.completion_status,
            result.summary
        ))
        self.conn.commit()
    
    def query_entities(self, entity_type: str = None, source_file: str = None) -> List[Dict]:
        """Query entities with optional filters"""
        query = "SELECT * FROM entities WHERE 1=1"
        params = []
        
        if entity_type:
            query += " AND type = ?"
            params.append(entity_type)
        
        if source_file:
            query += " AND source_file = ?"
            params.append(source_file)
        
        cursor = self.conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_graph_networkx(self):
        """Export graph to NetworkX format if available"""
        if not hasattr(nx, 'Graph') or nx.Graph is None:
            return None
        
        G = nx.Graph()
        
        # Add nodes (entities)
        entities = self.query_entities()
        for entity in entities:
            G.add_node(entity['id'], 
                      name=entity['name'],
                      type=entity['type'],
                      confidence=entity['confidence'])
        
        # Add edges (relationships)
        cursor = self.conn.execute("SELECT * FROM relationships")
        for row in cursor.fetchall():
            G.add_edge(row[1], row[2],  # source_entity, target_entity
                      relationship_type=row[3],
                      confidence=row[5])
        
        return G
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM entities")
        stats['total_entities'] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM relationships") 
        stats['total_relationships'] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM extraction_logs")
        stats['total_extractions'] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT AVG(confidence) FROM extraction_logs")
        avg_conf = cursor.fetchone()[0]
        stats['average_confidence'] = round(avg_conf, 3) if avg_conf else 0
        
        cursor = self.conn.execute("SELECT type, COUNT(*) FROM entities GROUP BY type")
        stats['entity_types'] = dict(cursor.fetchall())
        
        return stats

class HaikuKnowledgeExtractor:
    """Haiku-powered knowledge extraction subagent"""
    
    def __init__(self, 
                 anthropic_api_key: str = None,
                 db_path: str = "knowledge_graph.db",
                 output_dir: str = "docs/ai-generated",
                 cost_limit_daily: float = 2.00,
                 enable_caching: bool = True):
        
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None
        
        self.db = LightweightGraphDB(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.cost_limit_daily = cost_limit_daily
        self.enable_caching = enable_caching
        self.daily_cost = 0.0
        
        # Haiku pricing (as of 2025)
        self.haiku_input_cost = 0.25 / 1_000_000  # $0.25 per 1M input tokens
        self.haiku_output_cost = 1.25 / 1_000_000  # $1.25 per 1M output tokens
        
        # File filtering patterns - prioritize source code over docs/configs
        self.core_source_extensions = {'.java', '.kt', '.py', '.js', '.ts'}  # High priority
        self.config_extensions = {'.xml', '.yml', '.yaml'}  # Medium priority (pom.xml, etc.)
        self.doc_extensions = {'.md', '.json'}  # Low priority - limit quantity
        self.source_file_extensions = self.core_source_extensions | self.config_extensions | self.doc_extensions
        self.ignored_patterns = {
            # Compiled/Generated files
            '.class', '.jar', '.war', '.ear', '.pyc', '.pyo', '__pycache__',
            # Build directories  
            'target/', 'build/', 'dist/', 'node_modules/', '.gradle/',
            # IDE files
            '.idea/', '.vscode/', '.eclipse/', '*.iml',
            # Version control
            '.git/', '.svn/', '.hg/',
            # Logs and temp
            '*.log', 'tmp/', 'temp/', '.tmp'
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed based on extension, size, and .gitignore patterns"""
        
        # Check against ignored patterns first
        file_str = str(file_path).lower()
        for pattern in self.ignored_patterns:
            if pattern in file_str or file_str.endswith(pattern.rstrip('/')):
                return False
        
        # Check if it's a source file extension
        if file_path.suffix.lower() not in self.source_file_extensions:
            return False
        
        # Skip very large files (>1MB)  
        try:
            if file_path.stat().st_size > 1_000_000:
                return False
        except:
            return False
        
        return True
    
    def get_file_priority(self, file_path: Path) -> int:
        """Get processing priority for file (lower number = higher priority)"""
        extension = file_path.suffix.lower()
        
        # Priority 1: Core source files (architectural insight)
        if extension in self.core_source_extensions:
            return 1
        # Priority 2: Essential config files (pom.xml, build configs)
        elif extension in self.config_extensions and ('pom.xml' in str(file_path) or 'build.gradle' in str(file_path) or 'application.yml' in str(file_path)):
            return 2
        # Priority 3: Other config files
        elif extension in self.config_extensions:
            return 3
        # Priority 4: Essential documentation (README, architecture docs)
        elif extension in self.doc_extensions and ('README' in str(file_path).upper() or 'ARCHITECTURE' in str(file_path).upper() or 'CLAUDE' in str(file_path).upper()):
            return 4
        # Priority 5: Other documentation (limit quantity)
        elif extension in self.doc_extensions:
            return 5
        else:
            return 6
    
    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding detection"""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        self.logger.warning(f"Could not read file {file_path} with any encoding")
        return None
    
    async def extract_knowledge_haiku(self, content: str, file_path: str) -> ExtractionResult:
        """Extract knowledge using Haiku API"""
        start_time = time.time()
        
        if not self.client:
            # Fallback heuristic extraction
            return self.extract_knowledge_heuristic(content, file_path, start_time)
        
        # Check daily cost limit
        if self.daily_cost >= self.cost_limit_daily:
            self.logger.warning(f"Daily cost limit reached: ${self.daily_cost:.3f}")
            return self.extract_knowledge_heuristic(content, file_path, start_time)
        
        # Enhanced system prompt for Java/Kotlin/Maven specialized knowledge extraction
        system_prompt = """You are a READ-ONLY technical knowledge extraction specialist with expertise in Java, Kotlin, Maven, TypeScript, JavaScript, and software architecture.

🚨 CRITICAL CONSTRAINTS:
- YOU ARE STRICTLY FORBIDDEN from suggesting, recommending, or providing ANY file modifications
- YOU MAY ONLY READ and ANALYZE the provided content
- YOU MUST NOT provide refactoring suggestions, code improvements, or file changes
- YOUR ROLE is EXTRACTION ONLY - not modification, enhancement, or optimization
- VIOLATION of read-only constraints is STRICTLY PROHIBITED

Analyze the provided text and extract:
1. ENTITIES: Key concepts, technologies, classes, functions, components, interfaces, types
2. RELATIONSHIPS: How entities relate (inheritance, implementation, imports, dependencies, usage)
3. SUMMARY: Concise overview of main topics and architectural patterns (ANALYSIS ONLY, NO SUGGESTIONS)

ENTITY TYPES (use most specific):
- class: Java/Kotlin classes and constructors
- abstract_class: Abstract Java/Kotlin classes
- interface: Java/Kotlin interfaces
- function: Functions, methods, and Kotlin functions
- enum: Java/Kotlin enumerations
- annotation: Java/Kotlin annotations (@Override, @Component, etc.)
- package: Java/Kotlin package declarations
- maven_dependency: Maven dependency declarations
- maven_plugin: Maven plugin configurations
- configuration: Spring/config beans and properties
- service: Service classes and components
- repository: Data access objects and repositories
- controller: MVC controllers and REST endpoints
- entity: JPA entities and data classes
- dto: Data transfer objects
- util: Utility classes and helper functions
- test: Test classes and methods
- module: Modules and components
- technology: External libraries, frameworks (Spring, Hibernate, etc.)
- concept: Business logic patterns and architectural concepts

RELATIONSHIP TYPES (use most specific):
- extends: Class inheritance
- implements: Interface implementation
- imports: Import relationships
- depends_on: Maven dependency relationships
- autowires: Spring dependency injection
- uses: Direct usage or method calls
- contains: Package/class containment
- configures: Configuration relationships
- calls: Method invocation
- inherits: Inheritance relationships
- composes: Composition relationships
- aggregates: Aggregation relationships

MAVEN SPECIFIC PATTERNS:
- Extract groupId, artifactId, version from pom.xml
- Identify parent-child module relationships
- Track plugin configurations and goals
- Note dependency scopes (compile, test, provided, runtime)

JAVA/KOTLIN SPECIFIC PATTERNS:
- Package structures and organization
- Spring annotations and configurations
- JPA entity relationships
- Test class patterns (JUnit, TestNG)
- Utility and helper class patterns

ERROR HANDLING: If JSON parsing fails or content is malformed, analyze as plain text and extract patterns. Focus on code structure over JSON validation.

Respond with valid JSON in this exact format:
{
  "entities": [
    {"name": "EntityName", "type": "class|interface|function|enum|annotation|package|maven_dependency", "description": "brief description"}
  ],
  "relationships": [
    {"source": "EntityA", "target": "EntityB", "type": "extends|implements|imports|uses|depends_on|autowires", "description": "relationship description"}
  ],
  "summary": "1-2 sentence overview focusing on architectural patterns and Maven structure",
  "confidence": 0.85,
  "completion_status": "success|partial|failed"
}

Prioritize Java/Kotlin/Maven patterns, Spring framework usage, and enterprise architecture patterns."""

        try:
            # Truncate very long content to manage costs
            if len(content) > 8000:
                content = content[:8000] + "\n... [TRUNCATED]"
            
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                temperature=0.1,
                system=system_prompt,
                messages=[{
                    "role": "user", 
                    "content": f"File: {file_path}\n\nContent:\n{content}"
                }]
            )
            
            # Calculate costs
            input_tokens = len(content.split()) * 1.3  # Rough estimate
            output_tokens = len(response.content[0].text.split()) * 1.3
            cost = (input_tokens * self.haiku_input_cost + 
                   output_tokens * self.haiku_output_cost)
            self.daily_cost += cost
            
            # Parse JSON response
            response_text = response.content[0].text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            data = json.loads(response_text)
            
            processing_time = time.time() - start_time
            
            return ExtractionResult(
                file_path=file_path,
                content_hash=self.get_content_hash(content),
                entities=data.get('entities', []),
                relationships=data.get('relationships', []),
                summary=data.get('summary', 'No summary available'),
                confidence=data.get('confidence', 0.0),
                processing_time=processing_time,
                token_usage=int(input_tokens + output_tokens),
                cost_estimate=cost,
                completion_status=data.get('completion_status', 'unknown')
            )
            
        except Exception as e:
            self.logger.error(f"Haiku extraction failed for {file_path}: {e}")
            return self.extract_knowledge_heuristic(content, file_path, start_time, str(e))
    
    def extract_knowledge_heuristic(self, content: str, file_path: str, 
                                  start_time: float, error_info: str = None) -> ExtractionResult:
        """Fallback heuristic knowledge extraction"""
        entities = []
        relationships = []
        
        # Extract Python classes and functions
        if file_path.endswith('.py'):
            class_matches = re.findall(r'class\s+([A-Za-z_][A-Za-z0-9_]*)', content)
            for class_name in class_matches:
                entities.append({
                    'name': class_name,
                    'type': 'class', 
                    'description': f'Python class defined in {Path(file_path).name}'
                })
            
            func_matches = re.findall(r'def\s+([A-Za-z_][A-Za-z0-9_]*)', content)
            for func_name in func_matches:
                entities.append({
                    'name': func_name,
                    'type': 'function',
                    'description': f'Python function defined in {Path(file_path).name}'
                })
        
        # Extract common technical terms
        tech_terms = re.findall(r'\b(API|SDK|HTTP|JSON|SQL|Docker|AWS|Azure|GCP|GraphQL|REST|gRPC)\b', content, re.IGNORECASE)
        for term in set(tech_terms):
            entities.append({
                'name': term.upper(),
                'type': 'technology',
                'description': f'Technology mentioned in {Path(file_path).name}'
            })
        
        # Generate summary
        lines = content.split('\n')[:10]  # First 10 lines
        summary = f"File contains {len(entities)} extracted entities. " + ' '.join(lines)[:200] + "..."
        
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            file_path=file_path,
            content_hash=self.get_content_hash(content),
            entities=entities,
            relationships=relationships,
            summary=summary,
            confidence=0.6 if not error_info else 0.3,
            processing_time=processing_time,
            token_usage=0,
            cost_estimate=0.0,
            completion_status='heuristic_fallback' if not error_info else 'failed',
            error_info=error_info
        )
    
    async def process_file(self, file_path: Path) -> Optional[ExtractionResult]:
        """Process a single file for knowledge extraction"""
        if not self.should_process_file(file_path):
            return None
        
        content = self.read_file_content(file_path)
        if not content:
            return None
        
        # Check cache
        content_hash = self.get_content_hash(content)
        if self.enable_caching:
            cursor = self.db.conn.execute(
                "SELECT * FROM extraction_logs WHERE content_hash = ? ORDER BY created_at DESC LIMIT 1",
                (content_hash,)
            )
            cached = cursor.fetchone()
            if cached:
                self.logger.info(f"Using cached extraction for {file_path}")
                return None  # Already processed
        
        self.logger.info(f"Processing file: {file_path}")
        result = await self.extract_knowledge_haiku(content, str(file_path))
        
        # Store in database
        entities = []
        for entity_data in result.entities:
            entity = KnowledgeEntity(
                id=f"{result.content_hash}_{entity_data['name']}",
                name=entity_data['name'],
                type=entity_data['type'],
                description=entity_data['description'],
                attributes={},
                source_file=str(file_path),
                confidence=result.confidence
            )
            entities.append(entity)
        
        relationships = []
        for rel_data in result.relationships:
            relationship = KnowledgeRelationship(
                id=f"{result.content_hash}_{rel_data.get('source', '')}_{rel_data.get('target', '')}",
                source_entity=f"{result.content_hash}_{rel_data.get('source', '')}",
                target_entity=f"{result.content_hash}_{rel_data.get('target', '')}",
                relationship_type=rel_data.get('type', 'relates_to'),
                description=rel_data.get('description', ''),
                confidence=result.confidence,
                source_file=str(file_path)
            )
            relationships.append(relationship)
        
        self.db.store_entities(entities)
        self.db.store_relationships(relationships)
        self.db.log_extraction(result)
        
        return result
    
    async def scan_directory(self, directory: Path, max_files: int = 100) -> List[ExtractionResult]:
        """Scan directory and extract knowledge from files with priority ordering"""
        results = []
        processed_count = 0
        
        self.logger.info(f"Scanning directory: {directory}")
        
        # Collect all files with priorities
        files_with_priority = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and self.should_process_file(file_path):
                priority = self.get_file_priority(file_path)
                files_with_priority.append((priority, file_path))
        
        # Sort by priority (lower number = higher priority)
        files_with_priority.sort(key=lambda x: (x[0], x[1].name))
        
        self.logger.info(f"Found {len(files_with_priority)} eligible files, processing with priority ordering")
        
        for priority, file_path in files_with_priority:
            if processed_count >= max_files:
                self.logger.info(f"Reached max files limit: {max_files}")
                break
            
            result = await self.process_file(file_path)
            if result:
                results.append(result)
                processed_count += 1
                self.logger.info(f"Processed {file_path} (priority {priority})")
        
        self.logger.info(f"Processed {len(results)} files successfully")
        return results
    
    def generate_report(self, results: List[ExtractionResult], group_name: str) -> str:
        """Generate comprehensive report of extraction results"""
        timestamp = datetime.now().isoformat()
        
        # Calculate statistics
        total_files = len(results)
        total_entities = sum(len(r.entities) for r in results)
        total_relationships = sum(len(r.relationships) for r in results)
        avg_confidence = sum(r.confidence for r in results) / total_files if total_files > 0 else 0
        total_cost = sum(r.cost_estimate for r in results)
        avg_processing_time = sum(r.processing_time for r in results) / total_files if total_files > 0 else 0
        
        # Status distribution
        status_counts = {}
        for result in results:
            status_counts[result.completion_status] = status_counts.get(result.completion_status, 0) + 1
        
        # Entity types distribution  
        entity_types = {}
        for result in results:
            for entity in result.entities:
                entity_type = entity['type']
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # Generate report
        report = f"""# Knowledge Extraction Report: {group_name}

**Generated**: {timestamp}
**Extraction Agent**: Haiku-Powered Knowledge Extractor v1.0

## 📊 Summary Statistics

- **Files Processed**: {total_files}
- **Total Entities**: {total_entities}
- **Total Relationships**: {total_relationships}
- **Average Confidence**: {avg_confidence:.3f}
- **Total Cost**: ${total_cost:.4f}
- **Avg Processing Time**: {avg_processing_time:.2f}s per file

## 📈 Processing Status

{chr(10).join(f"- **{status}**: {count}" for status, count in status_counts.items())}

## 🏷️ Entity Types Distribution

{chr(10).join(f"- **{entity_type}**: {count}" for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True))}

## 📋 File Processing Details

| File | Entities | Relationships | Confidence | Status |
|------|----------|---------------|------------|--------|
{chr(10).join(f"| `{Path(r.file_path).name}` | {len(r.entities)} | {len(r.relationships)} | {r.confidence:.2f} | {r.completion_status} |" for r in results)}

## 🎯 Quality Assessment

**Extraction Quality**: {"✅ Excellent" if avg_confidence >= 0.8 else "⚠️ Good" if avg_confidence >= 0.6 else "❌ Needs Improvement"}

**Completion Rate**: {(status_counts.get('success', 0) / total_files * 100 if total_files > 0 else 0):.1f}%

**Agent Performance**: The LLM extraction agent performed {"excellently" if avg_confidence >= 0.8 else "well" if avg_confidence >= 0.6 else "adequately"} with an average confidence of {avg_confidence:.1%}.

## 🔍 Notable Findings

{chr(10).join(f"- **{result.summary[:100]}...** (from `{Path(result.file_path).name}`)" for result in results[:5])}

## 💰 Cost Analysis

- **Total Cost**: ${total_cost:.4f}
- **Cost per File**: ${(total_cost / total_files if total_files > 0 else 0):.4f}
- **Cost per Entity**: ${(total_cost / total_entities if total_entities > 0 else 0):.4f}

---
*Generated by Haiku Knowledge Extraction Subagent - YOLO-FFMPEG-MCP Project*
"""
        return report
    
    def save_report(self, report: str, group_name: str):
        """Save report to organized output directory"""
        # Create group directory
        group_dir = self.output_dir / group_name.lower().replace(' ', '-').replace('/', '-')
        group_dir.mkdir(exist_ok=True)
        
        # Save main report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = group_dir / f"extraction_report_{timestamp}.md"
        report_file.write_text(report)
        
        # Save database statistics
        stats = self.db.get_statistics()
        stats_file = group_dir / f"database_stats_{timestamp}.json"
        stats_file.write_text(json.dumps(stats, indent=2))
        
        self.logger.info(f"Report saved to {report_file}")
        self.logger.info(f"Database stats saved to {stats_file}")
        
        return report_file

# CLI Interface for testing
async def main():
    """Test the knowledge extraction system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Haiku Knowledge Extraction Subagent")
    parser.add_argument("path", help="Path to scan (file or directory)")
    parser.add_argument("--group-name", default="test-scan", help="Group name for output organization")
    parser.add_argument("--max-files", type=int, default=50, help="Maximum files to process")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    
    args = parser.parse_args()
    
    extractor = HaikuKnowledgeExtractor(anthropic_api_key=args.api_key)
    
    scan_path = Path(args.path)
    
    if scan_path.is_file():
        results = [await extractor.process_file(scan_path)]
        results = [r for r in results if r is not None]
    else:
        results = await extractor.scan_directory(scan_path, max_files=args.max_files)
    
    if results:
        report = extractor.generate_report(results, args.group_name)
        report_file = extractor.save_report(report, args.group_name)
        
        print(f"\n✅ Knowledge extraction complete!")
        print(f"📊 Processed {len(results)} files")
        print(f"📄 Report saved to: {report_file}")
        
        # Print database stats
        stats = extractor.db.get_statistics()
        print(f"\n📈 Database Statistics:")
        print(f"   Entities: {stats['total_entities']}")
        print(f"   Relationships: {stats['total_relationships']}")
        print(f"   Average Confidence: {stats['average_confidence']}")
        
    else:
        print("❌ No files were successfully processed")

if __name__ == "__main__":
    asyncio.run(main())