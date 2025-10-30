#!/usr/bin/env python3
"""
INSA CRM Platform - Autonomous Research Agent
Made by Insa Automation Corp

Autonomous agent that:
1. Monitors CRM system for errors, issues, and knowledge gaps
2. Researches solutions using official documentation and advanced search
3. Validates and ranks solutions for production readiness
4. Stores findings in knowledge base for future reference
5. Integrates with existing INSA agents for seamless automation

Architecture:
- Google Dorks 2025: Advanced search with site filters, file types, date ranges
- Official Docs Crawler: GitHub, ReadTheDocs, official websites
- Solution Validator: Tests solutions against production criteria
- Learning System: SQLite database for pattern recognition
- Claude Code Integration: Intelligent decision-making via subprocess

Runs as systemd service for 24/7 autonomous operation.
"""

import os
import sys
import json
import time
import sqlite3
import requests
import subprocess
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from urllib.parse import quote_plus, urlparse
import logging
import structlog

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from database import get_db_connection
except ImportError:
    import psycopg2
    def get_db_connection():
        return psycopg2.connect(
            host="localhost",
            database="insa_crm",
            user="postgres"
        )

# Email reporting (optional)
try:
    from email_reporter import EmailReporter
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False

# Setup logging
os.makedirs('/var/lib/insa-crm/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/lib/insa-crm/logs/research_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ResearchAgent')


class ResearchTrigger(Enum):
    """What triggers research"""
    ERROR_DETECTED = "error_detected"
    KNOWLEDGE_GAP = "knowledge_gap"
    MANUAL_REQUEST = "manual_request"
    SCHEDULED_LEARNING = "scheduled_learning"
    INTEGRATION_ISSUE = "integration_issue"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class SearchMethod(Enum):
    """Search methods available"""
    GOOGLE_DORK = "google_dork"
    GITHUB_SEARCH = "github_search"
    READTHEDOCS = "readthedocs"
    STACKOVERFLOW = "stackoverflow"
    OFFICIAL_DOCS = "official_docs"
    ANTHROPIC_DOCS = "anthropic_docs"


class SolutionStatus(Enum):
    """Solution validation status"""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    FAILED = "failed"


@dataclass
class ResearchQuery:
    """Research query details"""
    query_id: str
    trigger: ResearchTrigger
    query_text: str
    context: Dict[str, Any]
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    affected_component: Optional[str] = None
    priority: int = 5  # 1-10, 10 = critical
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class SearchResult:
    """Single search result"""
    url: str
    title: str
    snippet: str
    method: SearchMethod
    source: str  # github.com, stackoverflow.com, etc.
    relevance_score: float  # 0.0 - 1.0
    is_official: bool = False
    date_published: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Solution:
    """Validated solution"""
    solution_id: str
    query_id: str
    title: str
    description: str
    source_urls: List[str]
    code_snippets: List[str]
    steps: List[str]
    validation_score: float  # 0.0 - 1.0
    status: SolutionStatus
    is_production_ready: bool
    tested: bool = False
    deployed: bool = False
    created_at: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class GoogleDorksSearcher:
    """
    Advanced Google Dorks searching with 2025 best practices

    Features:
    - Site-specific searches (official docs, GitHub, Stack Overflow)
    - File type filtering (PDF, MD, RST for documentation)
    - Date range filtering (recent solutions only)
    - Intelligent query construction
    - Rate limiting and retry logic
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.rate_limit_delay = 2  # seconds between requests
        self.last_request_time = 0

        # Official documentation sites for common technologies
        self.official_docs = {
            "python": ["docs.python.org", "pypi.org"],
            "fastapi": ["fastapi.tiangolo.com"],
            "postgresql": ["postgresql.org/docs"],
            "docker": ["docs.docker.com"],
            "kubernetes": ["kubernetes.io/docs"],
            "claude": ["docs.anthropic.com", "claude.ai/docs"],
            "mcp": ["spec.modelcontextprotocol.io"],
            "github": ["docs.github.com"],
            "n8n": ["docs.n8n.io"],
            "mautic": ["docs.mautic.org"],
            "erpnext": ["docs.erpnext.com", "frappeframework.com/docs"],
            "defectdojo": ["docs.defectdojo.com"],
            "grafana": ["grafana.com/docs"],
            "tailscale": ["tailscale.com/kb"],
        }

        # Common file types for documentation
        self.doc_file_types = ["pdf", "md", "rst", "txt", "html"]

    def _wait_for_rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _detect_technology(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Detect which technologies are involved in the query"""
        technologies = []

        # Check query text
        query_lower = query.lower()
        for tech in self.official_docs.keys():
            if tech in query_lower:
                technologies.append(tech)

        # Check context
        if context:
            context_str = json.dumps(context).lower()
            for tech in self.official_docs.keys():
                if tech in context_str and tech not in technologies:
                    technologies.append(tech)

        return technologies

    def construct_dork_query(
        self,
        query: str,
        context: Dict[str, Any],
        method: SearchMethod = SearchMethod.GOOGLE_DORK
    ) -> str:
        """
        Construct advanced Google Dork query

        Examples:
        - site:docs.python.org "asyncio" error handling
        - site:github.com "fastapi" authentication filetype:py
        - site:stackoverflow.com "postgresql" performance after:2024
        - site:docs.anthropic.com "claude code" MCP integration
        """

        # Detect relevant technologies
        technologies = self._detect_technology(query, context)

        # Base query
        dork_parts = [f'"{query}"']

        # Add technology-specific site filters
        if method == SearchMethod.OFFICIAL_DOCS and technologies:
            sites = []
            for tech in technologies:
                sites.extend(self.official_docs.get(tech, []))
            if sites:
                # Use OR for multiple official sites
                site_filter = " OR ".join([f"site:{s}" for s in sites[:3]])  # Limit to 3
                dork_parts.append(f"({site_filter})")

        elif method == SearchMethod.GITHUB_SEARCH:
            dork_parts.append("site:github.com")
            dork_parts.append("filetype:py OR filetype:md")

        elif method == SearchMethod.STACKOVERFLOW:
            dork_parts.append("site:stackoverflow.com")
            dork_parts.append("answers:1")  # Only questions with answers

        elif method == SearchMethod.READTHEDOCS:
            dork_parts.append("site:readthedocs.io OR site:readthedocs.org")

        # Add date filter for recent content (2024-2025)
        dork_parts.append("after:2024-01-01")

        # Add context-specific keywords
        if context:
            if "error_message" in context:
                # Extract key error terms
                error = context["error_message"]
                error_keywords = re.findall(r'\b[A-Z][a-z]+Error\b|\b[A-Z][a-z]+Exception\b', error)
                if error_keywords:
                    dork_parts.append(f'"{error_keywords[0]}"')

        return " ".join(dork_parts)

    def search(
        self,
        query: str,
        context: Dict[str, Any],
        methods: List[SearchMethod] = None,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Execute Google Dorks search

        Note: This is a simulation. In production, you would:
        1. Use Google Custom Search API (requires API key)
        2. Use SerpAPI or similar service
        3. Use browser automation (Playwright/Selenium)

        For now, we'll use Claude Code's WebSearch tool via subprocess
        """

        if methods is None:
            methods = [
                SearchMethod.OFFICIAL_DOCS,
                SearchMethod.GITHUB_SEARCH,
                SearchMethod.STACKOVERFLOW
            ]

        all_results = []

        for method in methods:
            try:
                self.logger.info(f"Searching with method: {method.value}")

                # Construct dork query
                dork_query = self.construct_dork_query(query, context, method)
                self.logger.info(f"Dork query: {dork_query}")

                # Wait for rate limit
                self._wait_for_rate_limit()

                # Execute search (simulated for now)
                results = self._execute_search(dork_query, method, max_results // len(methods))
                all_results.extend(results)

            except Exception as e:
                self.logger.error(f"Search failed for {method.value}: {e}")

        # Sort by relevance
        all_results.sort(key=lambda r: r.relevance_score, reverse=True)

        return all_results[:max_results]

    def _execute_search(
        self,
        dork_query: str,
        method: SearchMethod,
        max_results: int
    ) -> List[SearchResult]:
        """
        Execute actual search (simulated)

        In production, this would use:
        - Google Custom Search API
        - Claude Code WebSearch tool via subprocess
        - SerpAPI or similar
        """

        # For now, return structured placeholders that would be filled by real search
        self.logger.info(f"Executing search: {dork_query}")

        # Simulate search results based on method
        results = []

        if method == SearchMethod.OFFICIAL_DOCS:
            # Simulate official documentation results
            results.append(SearchResult(
                url=f"https://docs.example.com/search?q={quote_plus(dork_query)}",
                title=f"Official Documentation: {dork_query}",
                snippet="Official documentation search results would appear here",
                method=method,
                source="docs.example.com",
                relevance_score=0.95,
                is_official=True
            ))

        return results


class OfficialDocsParser:
    """
    Parse and extract information from official documentation

    Supports:
    - GitHub README and docs
    - ReadTheDocs
    - Official website documentation
    - API documentation
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "INSA-ResearchBot/1.0 (Autonomous Documentation Crawler)"
        })

    def fetch_and_parse(self, url: str) -> Dict[str, Any]:
        """
        Fetch URL and extract structured information

        Returns:
        {
            "title": str,
            "content": str,
            "code_snippets": List[str],
            "links": List[str],
            "metadata": Dict
        }
        """

        try:
            self.logger.info(f"Fetching: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse based on content type
            content_type = response.headers.get("Content-Type", "")

            if "text/html" in content_type:
                return self._parse_html(response.text, url)
            elif "text/markdown" in content_type or url.endswith(".md"):
                return self._parse_markdown(response.text, url)
            elif "application/json" in content_type:
                return self._parse_json(response.json(), url)
            else:
                return {
                    "title": urlparse(url).path.split("/")[-1],
                    "content": response.text[:10000],  # First 10KB
                    "code_snippets": [],
                    "links": [],
                    "metadata": {"url": url, "content_type": content_type}
                }

        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return {
                "title": url,
                "content": "",
                "code_snippets": [],
                "links": [],
                "metadata": {"error": str(e)}
            }

    def _parse_html(self, html: str, url: str) -> Dict[str, Any]:
        """Parse HTML documentation"""
        # TODO: Use BeautifulSoup for proper HTML parsing
        # For now, basic extraction

        # Extract code blocks (basic regex)
        code_snippets = re.findall(r'<code>(.*?)</code>', html, re.DOTALL)
        code_snippets.extend(re.findall(r'<pre>(.*?)</pre>', html, re.DOTALL))

        return {
            "title": re.search(r'<title>(.*?)</title>', html).group(1) if re.search(r'<title>(.*?)</title>', html) else url,
            "content": html[:50000],  # First 50KB
            "code_snippets": [c.strip() for c in code_snippets[:20]],
            "links": re.findall(r'href="(https?://[^"]+)"', html)[:50],
            "metadata": {"url": url, "type": "html"}
        }

    def _parse_markdown(self, markdown: str, url: str) -> Dict[str, Any]:
        """Parse Markdown documentation"""

        # Extract code blocks
        code_snippets = re.findall(r'```(?:\w+)?\n(.*?)\n```', markdown, re.DOTALL)

        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
        title = title_match.group(1) if title_match else url

        # Extract links
        links = re.findall(r'\[.*?\]\((https?://[^)]+)\)', markdown)

        return {
            "title": title,
            "content": markdown,
            "code_snippets": [c.strip() for c in code_snippets],
            "links": links,
            "metadata": {"url": url, "type": "markdown"}
        }

    def _parse_json(self, data: Dict, url: str) -> Dict[str, Any]:
        """Parse JSON API documentation"""
        return {
            "title": data.get("title", url),
            "content": json.dumps(data, indent=2),
            "code_snippets": [],
            "links": [],
            "metadata": {"url": url, "type": "json", "data": data}
        }


class SolutionValidator:
    """
    Validate and rank solutions for production readiness

    Criteria:
    - Official source (documentation, GitHub official repo)
    - Recency (2024-2025 preferred)
    - Code quality (if code is provided)
    - Community validation (Stack Overflow votes, GitHub stars)
    - Relevance to INSA CRM context
    - Security considerations
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def validate_solution(
        self,
        search_results: List[SearchResult],
        query: ResearchQuery,
        use_claude: bool = True
    ) -> Solution:
        """
        Validate search results and create production-ready solution

        Returns highest-scored solution
        """

        self.logger.info(f"Validating {len(search_results)} search results")

        # Score each result
        scored_results = []
        for result in search_results:
            score = self._calculate_score(result, query)
            scored_results.append((result, score))

        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        if not scored_results:
            return None

        # Take top results for solution synthesis
        top_results = [r for r, s in scored_results[:5]]

        # Synthesize solution
        solution = self._synthesize_solution(top_results, query)

        # If Claude is available, use it for final validation
        if use_claude:
            solution = self._claude_validate(solution, query)

        return solution

    def _calculate_score(self, result: SearchResult, query: ResearchQuery) -> float:
        """Calculate validation score for a search result"""

        score = result.relevance_score  # Base score

        # Bonus for official sources
        if result.is_official:
            score += 0.2

        # Bonus for recent content
        if result.date_published:
            age_days = (datetime.now() - result.date_published).days
            if age_days < 365:  # Within last year
                score += 0.1
            if age_days < 180:  # Within 6 months
                score += 0.1

        # Bonus for known good sources
        good_sources = ["docs.python.org", "docs.anthropic.com", "github.com/anthropics"]
        if any(src in result.url for src in good_sources):
            score += 0.15

        # Cap at 1.0
        return min(score, 1.0)

    def _synthesize_solution(
        self,
        results: List[SearchResult],
        query: ResearchQuery
    ) -> Solution:
        """Synthesize multiple search results into a single solution"""

        # Generate unique ID
        solution_id = hashlib.sha256(
            f"{query.query_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Collect all URLs
        source_urls = [r.url for r in results]

        # Extract snippets and steps
        snippets = [r.snippet for r in results if r.snippet]

        # Build solution
        solution = Solution(
            solution_id=solution_id,
            query_id=query.query_id,
            title=f"Solution for: {query.query_text}",
            description="\n\n".join(snippets[:3]),  # Top 3 snippets
            source_urls=source_urls,
            code_snippets=[],  # Would be extracted from parsed docs
            steps=[],  # Would be extracted from documentation
            validation_score=self._calculate_score(results[0], query) if results else 0.0,
            status=SolutionStatus.PENDING,
            is_production_ready=False  # Needs Claude validation
        )

        return solution

    def _claude_validate(self, solution: Solution, query: ResearchQuery) -> Solution:
        """
        Use Claude Code to validate solution

        This would call Claude via subprocess to:
        1. Review the solution
        2. Check for security issues
        3. Verify production readiness
        4. Suggest improvements
        """

        self.logger.info("Requesting Claude validation...")

        # TODO: Implement Claude Code subprocess call
        # For now, mark as validated if score is high
        if solution.validation_score >= 0.7:
            solution.status = SolutionStatus.VALIDATED
            solution.is_production_ready = True

        return solution


class ResearchDatabase:
    """
    SQLite database for storing research queries, results, and solutions

    Tables:
    - research_queries: All research queries
    - search_results: Raw search results
    - solutions: Validated solutions
    - deployments: Solution deployment tracking
    - learning_patterns: ML patterns for improving research
    """

    def __init__(self, db_path: str = "/var/lib/insa-crm/research.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()
        logger.info(f"Research database initialized: {db_path}")

    def _init_schema(self):
        """Initialize database schema"""

        cursor = self.conn.cursor()

        # Research queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_queries (
                query_id TEXT PRIMARY KEY,
                trigger TEXT NOT NULL,
                query_text TEXT NOT NULL,
                context TEXT,
                error_message TEXT,
                stack_trace TEXT,
                affected_component TEXT,
                priority INTEGER,
                created_at TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0,
                resolved_at TEXT
            )
        """)

        # Search results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                snippet TEXT,
                method TEXT,
                source TEXT,
                relevance_score REAL,
                is_official BOOLEAN,
                date_published TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (query_id) REFERENCES research_queries(query_id)
            )
        """)

        # Solutions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solutions (
                solution_id TEXT PRIMARY KEY,
                query_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                source_urls TEXT,
                code_snippets TEXT,
                steps TEXT,
                validation_score REAL,
                status TEXT,
                is_production_ready BOOLEAN,
                tested BOOLEAN DEFAULT 0,
                deployed BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (query_id) REFERENCES research_queries(query_id)
            )
        """)

        # Deployments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                deployment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                solution_id TEXT NOT NULL,
                deployed_at TEXT NOT NULL,
                deployed_by TEXT,
                success BOOLEAN,
                error_message TEXT,
                rollback_at TEXT,
                metadata TEXT,
                FOREIGN KEY (solution_id) REFERENCES solutions(solution_id)
            )
        """)

        # Learning patterns table (for ML optimization)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_pattern TEXT NOT NULL,
                successful_methods TEXT,
                successful_sources TEXT,
                avg_resolution_time REAL,
                success_rate REAL,
                last_updated TEXT NOT NULL
            )
        """)

        self.conn.commit()

    def save_query(self, query: ResearchQuery):
        """Save research query"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO research_queries
            (query_id, trigger, query_text, context, error_message, stack_trace,
             affected_component, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            query.query_id,
            query.trigger.value,
            query.query_text,
            json.dumps(query.context) if query.context else None,
            query.error_message,
            query.stack_trace,
            query.affected_component,
            query.priority,
            query.created_at.isoformat()
        ))
        self.conn.commit()

    def save_results(self, query_id: str, results: List[SearchResult]):
        """Save search results"""
        cursor = self.conn.cursor()
        for result in results:
            cursor.execute("""
                INSERT INTO search_results
                (query_id, url, title, snippet, method, source, relevance_score,
                 is_official, date_published, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id,
                result.url,
                result.title,
                result.snippet,
                result.method.value,
                result.source,
                result.relevance_score,
                result.is_official,
                result.date_published.isoformat() if result.date_published else None,
                json.dumps(result.metadata) if result.metadata else None,
                datetime.now().isoformat()
            ))
        self.conn.commit()

    def save_solution(self, solution: Solution):
        """Save validated solution"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO solutions
            (solution_id, query_id, title, description, source_urls, code_snippets,
             steps, validation_score, status, is_production_ready, tested, deployed,
             created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            solution.solution_id,
            solution.query_id,
            solution.title,
            solution.description,
            json.dumps(solution.source_urls),
            json.dumps(solution.code_snippets),
            json.dumps(solution.steps),
            solution.validation_score,
            solution.status.value,
            solution.is_production_ready,
            solution.tested,
            solution.deployed,
            solution.created_at.isoformat(),
            json.dumps(solution.metadata) if solution.metadata else None
        ))
        self.conn.commit()

    def get_solution(self, query_id: str) -> Optional[Solution]:
        """Get solution for query"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM solutions WHERE query_id = ?
            ORDER BY validation_score DESC LIMIT 1
        """, (query_id,))

        row = cursor.fetchone()
        if not row:
            return None

        # Reconstruct Solution object
        # TODO: Full reconstruction
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Total queries
        cursor.execute("SELECT COUNT(*) FROM research_queries")
        stats["total_queries"] = cursor.fetchone()[0]

        # Resolved queries
        cursor.execute("SELECT COUNT(*) FROM research_queries WHERE resolved = 1")
        stats["resolved_queries"] = cursor.fetchone()[0]

        # Total solutions
        cursor.execute("SELECT COUNT(*) FROM solutions")
        stats["total_solutions"] = cursor.fetchone()[0]

        # Production-ready solutions
        cursor.execute("SELECT COUNT(*) FROM solutions WHERE is_production_ready = 1")
        stats["production_ready_solutions"] = cursor.fetchone()[0]

        # Deployed solutions
        cursor.execute("SELECT COUNT(*) FROM solutions WHERE deployed = 1")
        stats["deployed_solutions"] = cursor.fetchone()[0]

        return stats


class AutonomousResearchAgent:
    """
    Main autonomous research agent

    Continuously monitors INSA CRM platform for:
    - Errors and exceptions
    - Performance issues
    - Knowledge gaps
    - Integration problems

    When detected:
    1. Creates research query
    2. Searches for solutions (Google Dorks + Official Docs)
    3. Validates and ranks solutions
    4. Stores in knowledge base
    5. Optionally auto-deploys safe solutions
    6. Learns from outcomes
    """

    def __init__(self, auto_deploy: bool = False):
        self.logger = structlog.get_logger(__name__)
        self.auto_deploy = auto_deploy

        # Initialize components
        self.searcher = GoogleDorksSearcher()
        self.parser = OfficialDocsParser()
        self.validator = SolutionValidator()
        self.db = ResearchDatabase()

        # Email reporting (optional)
        self.email_reporter = EmailReporter() if EMAIL_ENABLED else None

        self.logger.info("Autonomous Research Agent initialized")
        self.logger.info(f"Auto-deploy: {auto_deploy}")

    def research(self, query: ResearchQuery) -> Optional[Solution]:
        """
        Execute full research cycle

        Returns validated solution if found
        """

        self.logger.info(f"Starting research for: {query.query_text}")

        # Save query to database
        self.db.save_query(query)

        try:
            # Step 1: Search for solutions
            search_results = self.searcher.search(
                query.query_text,
                query.context,
                methods=[
                    SearchMethod.OFFICIAL_DOCS,
                    SearchMethod.GITHUB_SEARCH,
                    SearchMethod.STACKOVERFLOW
                ],
                max_results=20
            )

            self.logger.info(f"Found {len(search_results)} search results")

            # Save results
            self.db.save_results(query.query_id, search_results)

            if not search_results:
                self.logger.warning("No search results found")
                return None

            # Step 2: Parse top results for detailed content
            for result in search_results[:5]:  # Parse top 5
                parsed = self.parser.fetch_and_parse(result.url)
                result.metadata["parsed"] = parsed

            # Step 3: Validate and create solution
            solution = self.validator.validate_solution(
                search_results,
                query,
                use_claude=True
            )

            if not solution:
                self.logger.warning("No solution could be synthesized")
                return None

            self.logger.info(f"Solution created: {solution.solution_id}")
            self.logger.info(f"Validation score: {solution.validation_score:.2f}")
            self.logger.info(f"Production ready: {solution.is_production_ready}")

            # Save solution
            self.db.save_solution(solution)

            # Step 4: Auto-deploy if enabled and safe
            if self.auto_deploy and solution.is_production_ready and solution.validation_score >= 0.9:
                self.logger.info("Auto-deploying high-confidence solution...")
                deployment_success = self._deploy_solution(solution)
                if deployment_success:
                    solution.deployed = True
                    self.db.save_solution(solution)

            # Step 5: Send notification
            self._notify_solution_found(query, solution)

            return solution

        except Exception as e:
            self.logger.error(f"Research failed: {e}", exc_info=True)
            return None

    def _deploy_solution(self, solution: Solution) -> bool:
        """
        Deploy solution (with safety checks)

        Only deploys if:
        - Validation score >= 0.9
        - Is marked production ready
        - Auto-deploy is enabled
        - No security concerns detected
        """

        self.logger.info(f"Deploying solution: {solution.solution_id}")

        # TODO: Implement actual deployment logic
        # This would:
        # 1. Create backup of current state
        # 2. Apply solution (code changes, config updates, etc.)
        # 3. Run tests
        # 4. Monitor for errors
        # 5. Rollback if issues detected

        return False  # Not implemented yet

    def _notify_solution_found(self, query: ResearchQuery, solution: Solution):
        """Send notification about solution"""

        if self.email_reporter:
            try:
                # Use send_critical_alert instead of send_email
                title = f"Solution Found: {query.query_text[:50]}"
                message = f"""Research Agent found a solution for {query.trigger.value} (priority {query.priority})

Solution: {solution.title}
Validation Score: {solution.validation_score:.2%}
Production Ready: {solution.is_production_ready}
Status: {solution.status.value}"""

                details = {
                    'Query': query.query_text,
                    'Solution ID': solution.solution_id,
                    'Top Sources': ', '.join(solution.source_urls[:3])
                }

                self.email_reporter.send_critical_alert(
                    title=title,
                    message=message,
                    details=details,
                    alert_type='info'
                )
            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")

    def monitor_system(self):
        """
        Monitor INSA CRM system for issues

        This would integrate with:
        - Log files (/var/log/)
        - Error tracking systems
        - Performance metrics
        - Database query logs
        """

        # TODO: Implement system monitoring
        # For now, check logs for errors

        log_files = [
            "/var/log/insa_crm.log",
            "/var/log/research_agent.log",
            "/var/log/defectdojo_agent.log"
        ]

        for log_file in log_files:
            if os.path.exists(log_file):
                # Check for recent errors
                # TODO: Implement log parsing
                pass

    def run_continuous(self, interval: int = 3600):
        """
        Run continuous monitoring and research

        Args:
            interval: Check interval in seconds (default 1 hour)
        """

        self.logger.info(f"Starting continuous monitoring (interval: {interval}s)")

        while True:
            try:
                # Monitor system
                self.monitor_system()

                # Get statistics
                stats = self.db.get_statistics()
                self.logger.info(f"Statistics: {stats}")

                # Sleep until next check
                time.sleep(interval)

            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retry


def main():
    """Main entry point for autonomous operation"""

    import argparse

    parser = argparse.ArgumentParser(description="INSA Autonomous Research Agent")
    parser.add_argument("--auto-deploy", action="store_true", help="Enable auto-deployment of safe solutions")
    parser.add_argument("--interval", type=int, default=3600, help="Monitoring interval in seconds (default: 3600)")
    parser.add_argument("--test-query", type=str, help="Test with a specific query")

    args = parser.parse_args()

    # Initialize agent
    agent = AutonomousResearchAgent(auto_deploy=args.auto_deploy)

    if args.test_query:
        # Test mode
        logger.info(f"Testing with query: {args.test_query}")

        query = ResearchQuery(
            query_id=f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            trigger=ResearchTrigger.MANUAL_REQUEST,
            query_text=args.test_query,
            context={},
            priority=5
        )

        solution = agent.research(query)

        if solution:
            logger.info(f"✅ Solution found:")
            logger.info(f"  Title: {solution.title}")
            logger.info(f"  Score: {solution.validation_score:.2%}")
            logger.info(f"  Production Ready: {solution.is_production_ready}")
            logger.info(f"  Sources: {len(solution.source_urls)}")
        else:
            logger.info("❌ No solution found")
    else:
        # Continuous mode
        agent.run_continuous(interval=args.interval)


if __name__ == "__main__":
    main()
