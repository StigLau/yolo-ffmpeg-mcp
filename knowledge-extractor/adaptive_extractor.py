#!/usr/bin/env python3
"""
Adaptive Knowledge Extractor
Uses Haiku to analyze user intent and adapt scanning strategy accordingly.
"""

import asyncio
import sys
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from knowledge_extractor import HaikuKnowledgeExtractor
from anthropic import AsyncAnthropic
import os

class AdaptiveKnowledgeExtractor:
    def __init__(self, base_folder: str, user_prompt: str):
        self.base_folder = Path(base_folder)
        self.user_prompt = user_prompt
        self.output_dir = self.base_folder / 'docs' / 'knowledge-analysis'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Haiku client for intent analysis
        api_key = os.getenv('ANTHROPIC_API_KEY')
        self.haiku_client = AsyncAnthropic(api_key=api_key) if api_key else None
        
        # Initialize the knowledge extractor
        self.extractor = HaikuKnowledgeExtractor(
            db_path=str(self.output_dir / 'knowledge.db'),
            output_dir=str(self.output_dir),
            cost_limit_daily=1.00  # Conservative limit for testing
        )
    
    async def analyze_user_intent(self) -> Dict:
        """Use Haiku to analyze user intent and determine optimal scanning strategy"""
        
        if not self.haiku_client:
            print("⚠️ No Haiku API key - using default strategy")
            return self.get_default_strategy()
        
        print("🧠 Analyzing user intent with Haiku...")
        
        intent_prompt = f"""You are a codebase analysis strategist. A user wants to analyze a codebase with this goal:

USER GOAL: "{self.user_prompt}"

Based on this goal, determine the optimal scanning strategy. Respond with JSON:

{{
  "focus_areas": ["area1", "area2"],
  "file_priorities": {{
    "high": [".java", ".py"],
    "medium": [".xml", ".yml"], 
    "low": [".md", ".json"]
  }},
  "keywords": ["spring", "controller", "service"],
  "max_files": 100,
  "strategy": "architecture|security|data|testing|documentation",
  "reasoning": "Why this strategy fits the user's goal"
}}

Focus areas can be: controllers, services, data-access, security, configuration, tests, documentation, utilities, models, apis

Strategies:
- architecture: Focus on main classes, interfaces, key patterns
- security: Focus on auth, permissions, validation, security configs
- data: Focus on entities, repositories, database interactions
- testing: Focus on test files and test patterns
- documentation: Focus on README, docs, architecture files

Keep max_files reasonable (50-200) based on the complexity of the goal."""

        try:
            response = await self.haiku_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.1,
                messages=[{"role": "user", "content": intent_prompt}]
            )
            
            response_text = response.content[0].text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            
            strategy = json.loads(response_text)
            print(f"🎯 Strategy: {strategy['strategy']}")
            print(f"🔍 Focus: {', '.join(strategy['focus_areas'])}")
            print(f"📊 Max files: {strategy['max_files']}")
            print(f"💡 Reasoning: {strategy['reasoning']}")
            
            return strategy
            
        except Exception as e:
            print(f"⚠️ Intent analysis failed: {e}")
            return self.get_default_strategy()
    
    def get_default_strategy(self) -> Dict:
        """Fallback strategy when Haiku analysis fails"""
        return {
            "focus_areas": ["architecture", "services"],
            "file_priorities": {
                "high": [".java", ".py", ".js", ".ts"],
                "medium": [".xml", ".yml", ".yaml"],
                "low": [".md", ".json"]
            },
            "keywords": [],
            "max_files": 50,
            "strategy": "architecture",
            "reasoning": "Default architectural analysis"
        }
    
    def discover_project_type(self) -> str:
        """Quick discovery of project type"""
        if (self.base_folder / 'pom.xml').exists():
            return "maven"
        elif (self.base_folder / 'build.gradle').exists():
            return "gradle"
        elif (self.base_folder / 'package.json').exists():
            return "npm"
        elif (self.base_folder / 'pyproject.toml').exists():
            return "python"
        elif (self.base_folder / 'Cargo.toml').exists():
            return "rust"
        else:
            return "generic"
    
    def get_relevant_files(self, strategy: Dict) -> List[Path]:
        """Get files based on strategy and user intent"""
        print(f"🔍 Discovering files in {self.base_folder}...")
        
        project_type = self.discover_project_type()
        print(f"📦 Project type: {project_type}")
        
        all_files = []
        priorities = strategy['file_priorities']
        max_files = strategy['max_files']
        focus_areas = strategy['focus_areas']
        keywords = strategy.get('keywords', [])
        
        # Collect files by priority
        high_files = []
        medium_files = []
        low_files = []
        
        for file_path in self.base_folder.rglob('*'):
            if not file_path.is_file():
                continue
                
            # Skip build directories and binaries
            skip_patterns = ['target/', 'build/', 'node_modules/', '.git/', '__pycache__/', '.class', '.jar']
            if any(pattern in str(file_path) for pattern in skip_patterns):
                continue
                
            extension = file_path.suffix.lower()
            
            # Priority classification
            if extension in priorities['high']:
                high_files.append(file_path)
            elif extension in priorities['medium']:
                medium_files.append(file_path)
            elif extension in priorities['low']:
                low_files.append(file_path)
        
        # Apply focus area filtering
        filtered_files = []
        
        for file_list, priority_name in [(high_files, 'high'), (medium_files, 'medium'), (low_files, 'low')]:
            for file_path in file_list:
                file_str = str(file_path).lower()
                
                # Focus area matching
                relevant = False
                for area in focus_areas:
                    if area in ['controllers', 'controller'] and ('controller' in file_str or 'rest' in file_str):
                        relevant = True
                    elif area in ['services', 'service'] and ('service' in file_str or 'business' in file_str):
                        relevant = True
                    elif area in ['data-access', 'data'] and ('repository' in file_str or 'dao' in file_str or 'entity' in file_str):
                        relevant = True
                    elif area in ['security'] and ('security' in file_str or 'auth' in file_str or 'login' in file_str):
                        relevant = True
                    elif area in ['configuration', 'config'] and ('config' in file_str or 'application' in file_str):
                        relevant = True
                    elif area in ['tests', 'testing'] and ('test' in file_str):
                        relevant = True
                    elif area in ['documentation'] and extension in ['.md', '.rst', '.adoc']:
                        relevant = True
                    elif area in ['architecture'] and priority_name == 'high':  # All high priority files for architecture
                        relevant = True
                
                # Keyword matching
                if keywords:
                    keyword_match = any(keyword.lower() in file_str for keyword in keywords)
                    if keyword_match:
                        relevant = True
                
                # For generic architecture analysis, include main source files
                if not focus_areas or 'architecture' in focus_areas:
                    if priority_name == 'high' or 'main' in file_str:
                        relevant = True
                
                if relevant:
                    filtered_files.append((file_path, priority_name))
        
        # Sort by priority and limit
        filtered_files.sort(key=lambda x: {'high': 1, 'medium': 2, 'low': 3}[x[1]])
        final_files = [f[0] for f in filtered_files[:max_files]]
        
        print(f"📊 File discovery results:")
        print(f"   Total discovered: {len(high_files + medium_files + low_files)}")
        print(f"   After filtering: {len(filtered_files)}")
        print(f"   Selected for analysis: {len(final_files)}")
        
        return final_files
    
    async def run_extraction(self) -> List:
        """Run the adaptive extraction process"""
        print(f"🚀 Starting adaptive knowledge extraction...")
        
        # Step 1: Analyze user intent
        strategy = await self.analyze_user_intent()
        
        # Step 2: Discover relevant files
        relevant_files = self.get_relevant_files(strategy)
        
        if not relevant_files:
            print("❌ No relevant files found for analysis")
            return []
        
        # Step 3: Process files with enhanced context
        print(f"⚙️ Processing {len(relevant_files)} files...")
        start_time = time.time()
        
        results = []
        for i, file_path in enumerate(relevant_files, 1):
            try:
                print(f"📄 Processing ({i}/{len(relevant_files)}): {file_path.name}")
                result = await self.extractor.process_file(file_path)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"⚠️ Error processing {file_path.name}: {e}")
                continue
        
        processing_time = time.time() - start_time
        
        # Step 4: Generate reports
        print(f"📋 Generating reports...")
        
        if results:
            total_cost = sum(r.cost_estimate for r in results)
            avg_confidence = sum(r.confidence for r in results) / len(results)
            
            print(f"✅ Extraction completed!")
            print(f"   Files processed: {len(results)}")
            print(f"   Total entities: {sum(len(r.entities) for r in results)}")
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Average confidence: {avg_confidence:.3f}")
            print(f"   Processing time: {processing_time/60:.1f} minutes")
            
            # Generate report
            report_path = self.extractor.generate_report(results, f"{self.base_folder.name}-analysis")
            print(f"📄 Report: {report_path}")
            
            # Generate focused summary based on user goal
            await self.generate_focused_summary(results, strategy)
            
        return results
    
    async def generate_focused_summary(self, results: List, strategy: Dict):
        """Generate a focused summary based on user's original goal"""
        if not self.haiku_client:
            return
        
        # Collect key findings
        all_entities = []
        for result in results:
            all_entities.extend(result.entities)
        
        # Create summary prompt
        entities_text = "\n".join([f"- {e['name']} ({e['type']}): {e.get('description', '')}" for e in all_entities[:50]])
        
        summary_prompt = f"""Based on the user's original goal: "{self.user_prompt}"

And these discovered entities from the codebase:
{entities_text}

Provide a focused summary that directly addresses the user's goal. Include:
1. Direct answer to their question/goal
2. Key findings and patterns discovered
3. Recommendations for further investigation
4. Any potential issues or gaps identified

Keep it concise and actionable."""

        try:
            response = await self.haiku_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                temperature=0.1,
                messages=[{"role": "user", "content": summary_prompt}]
            )
            
            focused_summary = response.content[0].text.strip()
            
            # Save focused summary
            summary_file = self.output_dir / 'focused_summary.md'
            with open(summary_file, 'w') as f:
                f.write(f"# Focused Analysis: {self.user_prompt}\n\n")
                f.write(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Strategy**: {strategy['strategy']}\n\n")
                f.write(focused_summary)
            
            print(f"🎯 Focused summary: {summary_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to generate focused summary: {e}")

async def main():
    if len(sys.argv) != 3:
        print("Usage: python adaptive_extractor.py <base-folder> <user-prompt>")
        sys.exit(1)
    
    base_folder = sys.argv[1]
    user_prompt = sys.argv[2]
    
    extractor = AdaptiveKnowledgeExtractor(base_folder, user_prompt)
    await extractor.run_extraction()

if __name__ == "__main__":
    asyncio.run(main())