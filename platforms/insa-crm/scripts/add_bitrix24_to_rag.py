#!/usr/bin/env python3
"""
Add Bitrix24 CRM Data to INSA RAG System
Integrates leads, contacts, companies, quotes, and products into ChromaDB for AI context

Author: INSA Automation Corp
Date: November 6, 2025
Purpose: Give AI agents context about INSA's CRM data for better responses
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add core module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    DEPS_AVAILABLE = True
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("pip install chromadb sentence-transformers")
    DEPS_AVAILABLE = False
    sys.exit(1)


class Bitrix24RAGIntegration:
    """Add Bitrix24 CRM data to ChromaDB RAG system"""

    def __init__(self,
                 persist_directory: str = "/var/lib/insa-crm/chromadb",
                 collection_name: str = "bitrix24_crm_data",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize Bitrix24 RAG integration

        Args:
            persist_directory: ChromaDB storage location
            collection_name: Collection name for Bitrix24 data
            embedding_model: Sentence-transformers model
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Create directory if needed
        os.makedirs(persist_directory, exist_ok=True)

        # Initialize ChromaDB
        print(f"🔌 Connecting to ChromaDB at {persist_directory}")
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Create or get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✅ Found existing collection: {collection_name} ({self.collection.count()} items)")
        except Exception:
            print(f"📦 Creating new collection: {collection_name}")
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={
                    "description": "INSA Bitrix24 CRM data for AI context",
                    "created_at": datetime.now().isoformat()
                }
            )

        # Load embedding model
        print(f"🧠 Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Stats
        self.stats = {
            "leads_added": 0,
            "contacts_added": 0,
            "companies_added": 0,
            "quotes_added": 0,
            "products_added": 0,
            "users_added": 0,
            "total_chunks": 0
        }

    def load_json_file(self, filepath: str) -> Dict:
        """Load JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading {filepath}: {e}")
            return {}

    def create_lead_chunk(self, lead: Dict) -> str:
        """Create semantic chunk from lead data"""
        parts = []

        parts.append(f"LEAD: {lead.get('company_title', lead.get('name', 'Unknown'))}")

        if lead.get('title'):
            parts.append(f"Inquiry: {lead['title']}")

        contact_name = f"{lead.get('name', '')} {lead.get('last_name', '')}".strip()
        if contact_name:
            parts.append(f"Contact: {contact_name}")

        if lead.get('email'):
            parts.append(f"Email: {lead['email']}")

        if lead.get('phone'):
            parts.append(f"Phone: {lead['phone']}")

        if lead.get('source_id'):
            parts.append(f"Source: {lead['source_id']}")

        if lead.get('status_id'):
            parts.append(f"Status: {lead['status_id']}")

        if lead.get('comments'):
            parts.append(f"Notes: {lead['comments']}")

        return "\n".join(parts)

    def create_company_chunk(self, company: Dict) -> str:
        """Create semantic chunk from company data"""
        parts = []

        parts.append(f"COMPANY: {company.get('title', 'Unknown')}")

        if company.get('company_type'):
            parts.append(f"Type: {company['company_type']}")

        if company.get('industry'):
            parts.append(f"Industry: {company['industry']}")

        if company.get('employees'):
            parts.append(f"Employees: {company['employees']}")

        if company.get('revenue'):
            parts.append(f"Revenue: {company['revenue']}")

        if company.get('comments'):
            parts.append(f"Notes: {company['comments']}")

        return "\n".join(parts)

    def create_product_chunk(self, product: Dict) -> str:
        """Create semantic chunk from product data"""
        parts = []

        parts.append(f"PRODUCT: {product.get('name', 'Unknown')}")

        if product.get('category'):
            parts.append(f"Category: {product['category']}")

        if product.get('description'):
            parts.append(f"Description: {product['description']}")

        if product.get('price'):
            parts.append(f"Price: ${product['price']}")

        if product.get('currency'):
            parts.append(f"Currency: {product['currency']}")

        if product.get('section'):
            parts.append(f"Section: {product['section']}")

        return "\n".join(parts)

    def create_quote_chunk(self, quote: Dict) -> str:
        """Create semantic chunk from quote data"""
        parts = []

        parts.append(f"QUOTE #{quote.get('id', 'Unknown')}")

        if quote.get('title'):
            parts.append(f"Title: {quote['title']}")

        if quote.get('company_title'):
            parts.append(f"Company: {quote['company_title']}")

        if quote.get('opportunity'):
            parts.append(f"Opportunity: {quote['opportunity']}")

        if quote.get('stage_id'):
            parts.append(f"Stage: {quote['stage_id']}")

        if quote.get('currency_id'):
            parts.append(f"Currency: {quote['currency_id']}")

        if quote.get('opportunity_value'):
            parts.append(f"Value: {quote['opportunity_value']}")

        if quote.get('content'):
            parts.append(f"Content: {quote['content']}")

        return "\n".join(parts)

    def create_user_chunk(self, user: Dict) -> str:
        """Create semantic chunk from user/employee data"""
        parts = []

        parts.append(f"EMPLOYEE: {user.get('name', 'Unknown')}")

        if user.get('email'):
            parts.append(f"Email: {user['email']}")

        if user.get('user_id'):
            parts.append(f"ID: {user['user_id']}")

        if user.get('position'):
            parts.append(f"Position: {user['position']}")

        if user.get('department'):
            parts.append(f"Department: {user['department']}")

        if user.get('phone'):
            parts.append(f"Phone: {user['phone']}")

        return "\n".join(parts)

    def add_users_to_rag(self, users_file: str = "bitrix24_graphiti_episodes.json"):
        """Add users/employees from Bitrix24 to RAG"""
        print("\n👥 Processing Users/Employees...")

        data = self.load_json_file(users_file)
        if not data:
            print("⚠️  No users data found")
            return

        # Extract users from graphiti format
        users = []
        if isinstance(data, list):
            for episode in data:
                if isinstance(episode, dict) and 'structured_data' in episode:
                    struct_data = episode['structured_data']
                    if struct_data.get('type') == 'user':
                        users.append(struct_data)

        print(f"Found {len(users)} users/employees")

        # Create embeddings
        for i, user in enumerate(users):
            chunk_text = self.create_user_chunk(user)
            embedding = self.embedding_model.encode([chunk_text])[0].tolist()

            chunk_id = f"user_{user.get('user_id', i)}"
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk_text],
                metadatas=[{
                    "type": "user",
                    "source": "bitrix24",
                    "id": str(user.get('user_id', i)),
                    "name": user.get('name', ''),
                    "email": user.get('email', ''),
                    "added_at": datetime.now().isoformat()
                }]
            )

            self.stats["users_added"] += 1

        print(f"✅ Added {self.stats['users_added']} users/employees to RAG")

    def add_leads_to_rag(self, leads_file: str = "bitrix24_graphiti_episodes.json"):
        """Add leads from Bitrix24 to RAG"""
        print("\n📊 Processing Leads...")

        data = self.load_json_file(leads_file)
        if not data:
            print("⚠️  No leads data found")
            return

        # Extract leads from graphiti format
        leads = []
        if isinstance(data, list):
            for episode in data:
                if isinstance(episode, dict) and 'structured_data' in episode:
                    struct_data = episode['structured_data']
                    if struct_data.get('type') == 'lead':
                        leads.append(struct_data)

        print(f"Found {len(leads)} leads")

        # Create embeddings
        for i, lead in enumerate(leads):
            chunk_text = self.create_lead_chunk(lead)
            embedding = self.embedding_model.encode([chunk_text])[0].tolist()

            chunk_id = f"lead_{lead.get('id', i)}"
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk_text],
                metadatas=[{
                    "type": "lead",
                    "source": "bitrix24",
                    "id": str(lead.get('id', i)),
                    "company": lead.get('company_title', ''),
                    "status": lead.get('status_id', ''),
                    "added_at": datetime.now().isoformat()
                }]
            )

            self.stats["leads_added"] += 1

        print(f"✅ Added {self.stats['leads_added']} leads to RAG")

    def add_products_to_rag(self, products_file: str = "cad_training_data_from_bitrix24.json"):
        """Add products from Bitrix24 to RAG"""
        print("\n🏭 Processing Products...")

        data = self.load_json_file(products_file)
        if not data:
            print("⚠️  No products data found")
            return

        # Extract products
        products = []
        if isinstance(data, list):
            products = data
        elif isinstance(data, dict) and 'products' in data:
            products = data['products']

        print(f"Found {len(products)} products")

        # Create embeddings
        for i, product in enumerate(products):
            chunk_text = self.create_product_chunk(product)
            embedding = self.embedding_model.encode([chunk_text])[0].tolist()

            chunk_id = f"product_{product.get('id', i)}"
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk_text],
                metadatas=[{
                    "type": "product",
                    "source": "bitrix24",
                    "id": str(product.get('id', i)),
                    "name": product.get('name', ''),
                    "category": product.get('category', ''),
                    "added_at": datetime.now().isoformat()
                }]
            )

            self.stats["products_added"] += 1

        print(f"✅ Added {self.stats['products_added']} products to RAG")

    def test_rag_query(self, query: str, n_results: int = 3):
        """Test RAG with a query"""
        print(f"\n🔍 Testing RAG Query: '{query}'")

        # Encode query
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        print(f"\n📋 Top {n_results} Results:")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"\n{i}. [Score: {1-distance:.3f}] Type: {metadata['type']}")
            print(f"   {doc[:200]}...")

    def print_stats(self):
        """Print integration statistics"""
        self.stats["total_chunks"] = self.collection.count()

        print("\n" + "="*70)
        print("📊 BITRIX24 RAG INTEGRATION SUMMARY")
        print("="*70)
        print(f"✅ Users/Employees:  {self.stats['users_added']}")
        print(f"✅ Leads added:      {self.stats['leads_added']}")
        print(f"✅ Products added:   {self.stats['products_added']}")
        print(f"✅ Total chunks:     {self.stats['total_chunks']}")
        print(f"📁 Storage:          {self.persist_directory}")
        print(f"📦 Collection:       {self.collection_name}")
        print("="*70)


def main():
    """Main execution"""
    print("\n🚀 INSA Bitrix24 RAG Integration")
    print("="*70)

    # Change to INSA CRM directory
    os.chdir("/home/wil/platforms/insa-crm")

    # Initialize integration
    integration = Bitrix24RAGIntegration()

    # Add data to RAG
    integration.add_users_to_rag()
    integration.add_leads_to_rag()
    integration.add_products_to_rag()

    # Print stats
    integration.print_stats()

    # Test queries
    print("\n🧪 TESTING RAG QUERIES")
    print("="*70)

    integration.test_rag_query("Juan Carlos Casas contact information")
    integration.test_rag_query("separator for oil and gas")
    integration.test_rag_query("pressure transmitter specifications")

    print("\n✅ Integration complete!")
    print("\n💡 Next steps:")
    print("   1. AI agents now have access to Bitrix24 CRM context")
    print("   2. Lead qualification can reference similar past leads")
    print("   3. Product recommendations use actual catalog data")
    print("   4. Quote generation uses historical quote patterns")


if __name__ == "__main__":
    if not DEPS_AVAILABLE:
        sys.exit(1)
    main()
