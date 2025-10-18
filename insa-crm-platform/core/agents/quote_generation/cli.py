#!/usr/bin/env python3
"""
INSA Quote Generation CLI
Command-line interface for testing quote generation
"""

import sys
import argparse
import json
from pathlib import Path
import structlog

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.quote_generation.quote_orchestrator import QuoteOrchestrator
from agents.quote_generation.config import config

# Configure logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(colors=True)
    ]
)

logger = structlog.get_logger()


def generate_quote_command(args):
    """Generate a quote from requirements"""
    orchestrator = QuoteOrchestrator()

    logger.info("Starting quote generation",
               customer=args.customer,
               source=args.source if args.file else "stdin")

    # Get requirements
    if args.file:
        requirement_source = args.file
        source_type = "auto"
    else:
        print("Enter requirements (press Ctrl+D when done):")
        requirement_source = sys.stdin.read()
        source_type = "text"

    # Customer context (optional)
    customer_context = None
    if args.existing_customer:
        customer_context = {
            "is_new_customer": False,
            "project_count": 3,
            "strategic_importance": 8,
            "price_sensitive": False
        }

    # Generate quote
    quote = orchestrator.generate_quote(
        requirement_source=requirement_source,
        customer_name=args.customer,
        customer_email=args.email,
        source_type=source_type,
        customer_context=customer_context,
        auto_approve_threshold=args.confidence_threshold
    )

    # Output quote
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(quote, f, indent=2)
        print(f"\n✅ Quote saved to: {args.output}")
    else:
        print("\n" + "="*80)
        print("QUOTE GENERATED")
        print("="*80)
        print(json.dumps(quote, indent=2))

    # Summary
    print("\n" + "="*80)
    print("QUOTE SUMMARY")
    print("="*80)
    print(f"Quote ID: {quote['quote_id']}")
    print(f"Customer: {quote['customer']['name']}")
    print(f"Total Price: ${quote['pricing']['pricing']['total']:,.2f} USD")
    print(f"Generation Time: {quote['metadata']['generation_time_seconds']}s")
    print(f"Confidence: {quote['approval']['overall_confidence']:.0%}")
    print(f"Win Probability: {quote['pricing']['win_probability']:.0%}")
    print(f"Requires Review: {'YES' if quote['approval']['requires_review'] else 'NO'}")
    print(f"Recommended Action: {quote['approval']['recommended_action']}")
    print("="*80)


def index_projects_command(args):
    """Index reference projects into RAG database"""
    orchestrator = QuoteOrchestrator()

    logger.info("Indexing reference projects")
    count = orchestrator.index_reference_projects()

    print(f"\n✅ Indexed {count} reference projects")

    # Show statistics
    stats = orchestrator.rag.get_statistics()
    print(f"\nRAG Database Statistics:")
    print(f"  Total Projects: {stats.get('total_projects', 0)}")
    print(f"  Collection: {stats.get('collection_name')}")
    print(f"  Storage: {stats.get('storage_path')}")


def list_quotes_command(args):
    """List generated quotes"""
    orchestrator = QuoteOrchestrator()

    quotes = orchestrator.list_quotes(limit=args.limit)

    if not quotes:
        print("No quotes found")
        return

    print(f"\n{'ID':<20} {'Customer':<30} {'Price':<15} {'Status':<10} {'Review'}")
    print("-" * 100)

    for q in quotes:
        review = "✓" if q['requires_review'] else "✗"
        print(f"{q['quote_id']:<20} {q['customer']:<30} ${q['total_price']:>12,.2f} {q['status']:<10} {review}")

    print(f"\nTotal: {len(quotes)} quotes")


def view_quote_command(args):
    """View a specific quote"""
    orchestrator = QuoteOrchestrator()

    quote = orchestrator.get_quote(args.quote_id)

    if not quote:
        print(f"Quote not found: {args.quote_id}")
        return

    print(json.dumps(quote, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="INSA AI Quote Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate quote from text input
  python cli.py generate --customer "ABC Manufacturing" --email "john@abc.com"

  # Generate quote from PDF file
  python cli.py generate --customer "XYZ Corp" --email "mary@xyz.com" --file rfp.pdf

  # Index reference projects
  python cli.py index

  # List recent quotes
  python cli.py list

  # View specific quote
  python cli.py view Q-20251018220000
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate a quote')
    generate_parser.add_argument('--customer', required=True, help='Customer name')
    generate_parser.add_argument('--email', required=True, help='Customer email')
    generate_parser.add_argument('--file', help='Requirements file (PDF, DOCX, TXT)')
    generate_parser.add_argument('--output', help='Output file for quote JSON')
    generate_parser.add_argument('--existing-customer', action='store_true',
                                help='Flag as existing customer for better pricing')
    generate_parser.add_argument('--confidence-threshold', type=float, default=0.85,
                                help='Auto-approve threshold (default: 0.85)')
    generate_parser.set_defaults(func=generate_quote_command)

    # Index command
    index_parser = subparsers.add_parser('index', help='Index reference projects')
    index_parser.set_defaults(func=index_projects_command)

    # List command
    list_parser = subparsers.add_parser('list', help='List recent quotes')
    list_parser.add_argument('--limit', type=int, default=20, help='Number of quotes to show')
    list_parser.set_defaults(func=list_quotes_command)

    # View command
    view_parser = subparsers.add_parser('view', help='View a specific quote')
    view_parser.add_argument('quote_id', help='Quote ID')
    view_parser.set_defaults(func=view_quote_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        logger.error("Command failed", error=str(e), command=args.command)
        sys.exit(1)


if __name__ == "__main__":
    main()
