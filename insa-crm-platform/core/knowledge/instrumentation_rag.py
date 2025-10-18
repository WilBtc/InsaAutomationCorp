"""
Industrial Instrumentation RAG System for CRM Agents
Retrieval-Augmented Generation using instrumentation knowledge base

This module provides a simple text-based RAG system that CRM agents can use
to query the industrial instrumentation reference book.

Author: INSA Automation Corp
Date: October 18, 2025
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentChunk:
    """A chunk of text from the instrumentation manual"""
    chunk_id: str
    content: str
    chapter: Optional[int] = None
    page_range: Optional[str] = None
    keywords: List[str] = None
    relevance_score: float = 0.0


class InstrumentationRAG:
    """
    RAG system for industrial instrumentation knowledge

    This is a lightweight implementation that uses TF-IDF and keyword matching.
    Future versions will use vector embeddings with Qdrant.
    """

    def __init__(self, knowledge_file: str = "/home/wil/instrumentacion-industrial-antonio-creus.txt"):
        """
        Initialize the RAG system

        Args:
            knowledge_file: Path to the extracted text file
        """
        self.knowledge_file = knowledge_file
        self.chunks: List[DocumentChunk] = []
        self.chapter_index: Dict[int, List[DocumentChunk]] = {}

        # Load and chunk the knowledge base
        if os.path.exists(knowledge_file):
            self._load_knowledge_base()
        else:
            print(f"⚠️ Knowledge file not found: {knowledge_file}")

    def _load_knowledge_base(self):
        """Load and chunk the instrumentation knowledge base"""
        print(f"📚 Loading instrumentation knowledge from {self.knowledge_file}...")

        with open(self.knowledge_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Split into chapters based on "Capítulo X" markers
        chapter_pattern = r'Capítulo (\d+)'
        chapters = re.split(chapter_pattern, content)

        chunk_id = 0
        for i in range(1, len(chapters), 2):  # Skip first element, then take pairs
            if i + 1 >= len(chapters):
                break

            chapter_num = int(chapters[i])
            chapter_content = chapters[i + 1]

            # Split chapter into paragraphs (every 10 lines ~ 500 words)
            lines = chapter_content.split('\n')
            paragraph_size = 10

            for j in range(0, len(lines), paragraph_size):
                paragraph_lines = lines[j:j + paragraph_size]
                paragraph = '\n'.join(paragraph_lines).strip()

                if len(paragraph) < 100:  # Skip very small chunks
                    continue

                # Extract keywords (simple approach: capitalize words, technical terms)
                keywords = self._extract_keywords(paragraph)

                chunk = DocumentChunk(
                    chunk_id=f"ch{chapter_num}_chunk{chunk_id}",
                    content=paragraph,
                    chapter=chapter_num,
                    keywords=keywords
                )

                self.chunks.append(chunk)

                # Index by chapter
                if chapter_num not in self.chapter_index:
                    self.chapter_index[chapter_num] = []
                self.chapter_index[chapter_num].append(chunk)

                chunk_id += 1

        print(f"✅ Loaded {len(self.chunks)} chunks from {len(self.chapter_index)} chapters")

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using simple heuristics"""
        keywords = set()

        # Common technical terms in industrial instrumentation
        technical_terms = [
            'PID', 'PLC', 'SCADA', 'HMI', 'DCS', 'RTU',
            'ISA', 'ISO', 'IEC', 'ANSI', 'ASME',
            'presión', 'temperatura', 'caudal', 'nivel', 'flujo',
            'transmisor', 'sensor', 'válvula', 'actuador', 'controlador',
            'calibración', 'medición', 'control', 'automático', 'proceso',
            'industrial', 'instrumentación', 'neumático', 'eléctrico',
            'analógico', 'digital', 'comunicación', 'protocolo'
        ]

        text_lower = text.lower()
        for term in technical_terms:
            if term.lower() in text_lower:
                keywords.add(term)

        # Extract capitalized words (potential important terms)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        keywords.update(capitalized[:5])  # Top 5 capitalized words

        return list(keywords)[:10]  # Max 10 keywords per chunk

    def query(self, query_text: str, top_k: int = 5, chapter: Optional[int] = None) -> List[DocumentChunk]:
        """
        Query the RAG system for relevant chunks

        Args:
            query_text: The search query
            top_k: Number of top results to return
            chapter: Optional chapter to filter results

        Returns:
            List of relevant DocumentChunks sorted by relevance
        """
        if not self.chunks:
            print("⚠️ No knowledge base loaded")
            return []

        # Simple keyword matching (TF-IDF would be better, vector embeddings even better)
        query_lower = query_text.lower()
        query_keywords = set(re.findall(r'\b\w{4,}\b', query_lower))  # Words with 4+ chars

        results = []
        search_pool = self.chunks if chapter is None else self.chapter_index.get(chapter, [])

        for chunk in search_pool:
            # Calculate relevance score
            score = 0.0
            content_lower = chunk.content.lower()

            # Exact phrase match (highest score)
            if query_lower in content_lower:
                score += 10.0

            # Keyword matches
            for keyword in query_keywords:
                if keyword in content_lower:
                    score += 2.0

            # Chunk keyword matches
            if chunk.keywords:
                for kw in chunk.keywords:
                    if kw.lower() in query_lower:
                        score += 1.5

            if score > 0:
                chunk.relevance_score = score
                results.append(chunk)

        # Sort by relevance and return top_k
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]

    def get_chapter(self, chapter_num: int) -> List[DocumentChunk]:
        """Get all chunks from a specific chapter"""
        return self.chapter_index.get(chapter_num, [])

    def get_context_for_agent(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get formatted context for AI agent prompts

        Args:
            query: The search query
            max_tokens: Maximum tokens to return (approximate)

        Returns:
            Formatted context string for injection into agent prompts
        """
        results = self.query(query, top_k=5)

        if not results:
            return "No relevant information found in instrumentation knowledge base."

        context_parts = ["# Industrial Instrumentation Knowledge\n"]
        current_tokens = 0

        for i, chunk in enumerate(results, 1):
            chunk_text = f"\n## Reference {i} (Chapter {chunk.chapter}, Score: {chunk.relevance_score:.1f})\n"
            chunk_text += f"{chunk.content}\n"

            # Approximate token count (1 token ~ 4 characters)
            chunk_tokens = len(chunk_text) // 4

            if current_tokens + chunk_tokens > max_tokens:
                break

            context_parts.append(chunk_text)
            current_tokens += chunk_tokens

        return '\n'.join(context_parts)

    def search_equipment(self, equipment_type: str) -> List[Tuple[str, str]]:
        """
        Search for specific equipment types

        Args:
            equipment_type: Type of equipment (e.g., "sensor presión", "válvula control")

        Returns:
            List of (equipment_name, description) tuples
        """
        results = self.query(equipment_type, top_k=10)
        equipment_list = []

        for chunk in results:
            # Extract sentences mentioning the equipment
            sentences = re.split(r'[.!?]', chunk.content)
            for sentence in sentences:
                if equipment_type.lower() in sentence.lower():
                    equipment_list.append((
                        equipment_type,
                        sentence.strip()
                    ))

        return equipment_list[:10]  # Max 10 results


# Global instance for easy import
instrumentation_rag = InstrumentationRAG()


# Example usage for CRM agents
def get_sensor_recommendation(application: str) -> str:
    """
    Get sensor recommendations for a specific application

    Example:
        recommendation = get_sensor_recommendation("medición de presión alta temperatura")
    """
    context = instrumentation_rag.get_context_for_agent(application, max_tokens=1000)
    return context


def get_control_strategy(process_type: str) -> str:
    """
    Get control strategy recommendations

    Example:
        strategy = get_control_strategy("control de temperatura en reactor")
    """
    # Query Chapter 9 (Control Automático)
    results = instrumentation_rag.query(process_type, top_k=3, chapter=9)

    if not results:
        return "No control strategy found for this process type."

    return f"# Control Strategy Recommendations\n\n" + \
           '\n\n'.join([f"## Option {i+1}\n{r.content}" for i, r in enumerate(results)])


def get_calibration_procedure(instrument_type: str) -> str:
    """
    Get calibration procedures for instruments

    Example:
        procedure = get_calibration_procedure("transmisor de presión")
    """
    # Query Chapter 10 (Calibración)
    results = instrumentation_rag.query(instrument_type, top_k=3, chapter=10)

    if not results:
        return "No calibration procedure found for this instrument type."

    return f"# Calibration Procedures\n\n" + \
           '\n\n'.join([f"## Step {i+1}\n{r.content}" for i, r in enumerate(results)])


if __name__ == "__main__":
    # Test the RAG system
    print("\n🧪 Testing Instrumentation RAG System\n")
    print("=" * 60)

    # Test 1: General query
    print("\n📝 Test 1: Searching for 'transmisor de presión'...")
    results = instrumentation_rag.query("transmisor de presión", top_k=3)
    for i, chunk in enumerate(results, 1):
        print(f"\nResult {i} (Score: {chunk.relevance_score:.1f}, Chapter {chunk.chapter}):")
        print(chunk.content[:200] + "...")

    # Test 2: Get context for agent
    print("\n" + "=" * 60)
    print("\n📝 Test 2: Get context for AI agent about 'válvula de control'...")
    context = instrumentation_rag.get_context_for_agent("válvula de control", max_tokens=500)
    print(context[:500] + "...")

    # Test 3: Chapter-specific search
    print("\n" + "=" * 60)
    print("\n📝 Test 3: Searching Chapter 9 (Control) for 'PID'...")
    results = instrumentation_rag.query("PID", top_k=2, chapter=9)
    for i, chunk in enumerate(results, 1):
        print(f"\nResult {i} (Score: {chunk.relevance_score:.1f}):")
        print(chunk.content[:200] + "...")

    print("\n" + "=" * 60)
    print("\n✅ RAG System Tests Complete!")
    print(f"\nTotal chunks: {len(instrumentation_rag.chunks)}")
    print(f"Total chapters: {len(instrumentation_rag.chapter_index)}")
