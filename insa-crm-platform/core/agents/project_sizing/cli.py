#!/usr/bin/env python3
"""
INSA Project Sizing CLI - Command-line interface
Provides easy access to project sizing functionality
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from sizing_orchestrator import SizingOrchestrator
from config import SIZING_RESULTS_DIR


def cmd_size(args):
    """
    Size a project from description
    """

    # Read description from file or stdin
    if args.file:
        with open(args.file, "r") as f:
            description = f.read()
    elif args.description:
        description = args.description
    else:
        print("📝 Enter project description (Ctrl+D when done):")
        description = sys.stdin.read()

    # Parse parameters if provided
    parameters = None
    if args.parameters:
        try:
            parameters = json.loads(args.parameters)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON parameters: {args.parameters}")
            return 1

    # Parse custom requirements
    custom_reqs = args.requirements.split(",") if args.requirements else None

    # Initialize orchestrator
    orchestrator = SizingOrchestrator()

    # Size the project
    print("\n🚀 Sizing project...\n")

    sizing = orchestrator.size_project(
        project_description=description,
        customer_name=args.customer,
        country=args.country,
        project_parameters=parameters,
        customer_requirements=custom_reqs,
        save_results=not args.no_save
    )

    # Display results
    if args.json:
        # JSON output
        print(json.dumps(sizing, indent=2))
    else:
        # Human-readable output
        print("\n" + "=" * 70)
        print("PROJECT SIZING RESULTS")
        print("=" * 70)

        print(f"\nSizing ID: {sizing['sizing_id']}")
        print(f"Generated: {sizing['timestamp']}")
        print(f"Generation Time: {sizing['generation_time_seconds']:.2f}s")

        print("\n" + "-" * 70)
        print("CLASSIFICATION")
        print("-" * 70)
        print(f"Type: {sizing['classification']['project_type']}")
        print(f"Complexity: {sizing['classification']['complexity']}")
        print(f"Disciplines: {len(sizing['classification']['required_disciplines'])}")
        print(f"Confidence: {sizing['classification']['overall_confidence']:.1%}")

        print("\n" + "-" * 70)
        print("ESTIMATION")
        print("-" * 70)
        print(f"Total Hours: {sizing['estimation']['total_hours']:.1f}h")
        print(f"Total Cost: ${sizing['estimation']['total_cost']:,.2f}")
        print(f"Duration: {sizing['estimation']['project_duration_weeks']} weeks")
        print(f"Confidence: {sizing['estimation']['overall_confidence']:.1%}")

        print("\n" + "-" * 70)
        print("PERSONNEL")
        print("-" * 70)
        for level, fte in sizing['estimation']['personnel_required'].items():
            print(f"  {level.replace('_', ' ').title()}: {fte:.2f} FTE")

        print("\n" + "-" * 70)
        print("DOCUMENTS")
        print("-" * 70)
        print(f"Total Documents: {sizing['documents']['total_documents']}")
        print(f"Templates Available: {len(sizing['documents']['templates_available'])}")

        print("\n" + "-" * 70)
        print("ASSESSMENT")
        print("-" * 70)
        print(f"Confidence Level: {sizing['assessment']['confidence_level']}")
        print(f"Ready for Quote: {'YES ✅' if sizing['assessment']['ready_for_quotation'] else 'NO ⚠️'}")

        if sizing['assessment']['risks']:
            print("\n⚠️  RISKS:")
            for risk in sizing['assessment']['risks']:
                print(f"  • {risk}")

        if sizing['assessment']['opportunities']:
            print("\n✨ OPPORTUNITIES:")
            for opp in sizing['assessment']['opportunities']:
                print(f"  • {opp}")

        print("\n" + "-" * 70)
        print("RECOMMENDED ACTIONS")
        print("-" * 70)
        for action in sizing['recommended_actions']:
            print(f"  {action}")

        if 'saved_to' in sizing:
            print("\n" + "=" * 70)
            print(f"💾 Results saved to:")
            print(f"   {sizing['saved_to']}")
            print(f"   {sizing['saved_to'].replace('_project_sizing.json', '_summary.txt')}")

    return 0


def cmd_list(args):
    """
    List saved project sizings
    """

    orchestrator = SizingOrchestrator()
    sizings = orchestrator.list_saved_sizings(limit=args.limit)

    if not sizings:
        print("No saved project sizings found.")
        return 0

    print(f"\n📊 Recent Project Sizings (showing {len(sizings)}):\n")

    print(f"{'ID':<20} {'Customer':<20} {'Type':<12} {'Hours':<8} {'Cost':<12} {'Conf':<6} {'Date'}")
    print("-" * 100)

    for sizing in sizings:
        print(
            f"{sizing['sizing_id']:<20} "
            f"{(sizing['customer'] or 'Unknown')[:19]:<20} "
            f"{sizing['project_type'][:11]:<12} "
            f"{sizing['total_hours']:<8.1f} "
            f"${sizing['total_cost']:<11,.0f} "
            f"{sizing['confidence']:<6.1%} "
            f"{sizing['timestamp'][:10]}"
        )

    return 0


def cmd_view(args):
    """
    View a saved project sizing
    """

    orchestrator = SizingOrchestrator()
    sizing = orchestrator.load_sizing(args.sizing_id)

    if not sizing:
        print(f"❌ Sizing not found: {args.sizing_id}")
        return 1

    if args.json:
        print(json.dumps(sizing, indent=2))
    else:
        # Display summary file
        summary_path = SIZING_RESULTS_DIR / f"{args.sizing_id}_summary.txt"
        if summary_path.exists():
            with open(summary_path, "r") as f:
                print(f.read())
        else:
            print(json.dumps(sizing, indent=2))

    return 0


def cmd_export(args):
    """
    Export sizing to ERPNext project
    """

    orchestrator = SizingOrchestrator()
    sizing = orchestrator.load_sizing(args.sizing_id)

    if not sizing:
        print(f"❌ Sizing not found: {args.sizing_id}")
        return 1

    print(f"\n🔄 Exporting sizing {args.sizing_id} to ERPNext...")
    print("\n⚠️  ERPNext integration not yet implemented (Phase 11 - pending)")
    print("\nManual steps:")
    erpnext_url = os.getenv("ERPNEXT_API_URL", "http://localhost:9000")
    print(f"1. Open ERPNext: {erpnext_url}")
    print("2. Create new Project")
    print(f"3. Import data from: {SIZING_RESULTS_DIR}/{args.sizing_id}_project_sizing.json")
    print(f"4. Estimated hours: {sizing['estimation']['total_hours']:.1f}")
    print(f"5. Estimated cost: ${sizing['estimation']['total_cost']:,.2f}")

    return 0


def main():
    """
    Main CLI entry point
    """

    parser = argparse.ArgumentParser(
        description="INSA AI Project Sizing Agent - Dimension projects automatically",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Size a project from description
  python cli.py size --description "Three-phase separator with PLC control"

  # Size from file
  python cli.py size --file project_description.txt --customer "Deilim Colombia"

  # Size with parameters
  python cli.py size --file desc.txt --parameters '{"io_count": 64, "tank_count": 3}'

  # List recent sizings
  python cli.py list

  # View a sizing
  python cli.py view SZ-20251019164530

  # Export to ERPNext
  python cli.py export SZ-20251019164530

© 2025 INSA Automation Corp - AI-Powered Project Sizing
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # ========================================================================
    # SIZE command
    # ========================================================================
    size_parser = subparsers.add_parser("size", help="Size a new project")
    size_parser.add_argument(
        "-d", "--description",
        help="Project description (or use --file or stdin)"
    )
    size_parser.add_argument(
        "-f", "--file",
        help="Read project description from file"
    )
    size_parser.add_argument(
        "-c", "--customer",
        help="Customer name"
    )
    size_parser.add_argument(
        "--country",
        default="colombia",
        choices=["colombia", "ecuador", "usa"],
        help="Project country (default: colombia)"
    )
    size_parser.add_argument(
        "-p", "--parameters",
        help='Project parameters as JSON (e.g., \'{"io_count": 64}\')'
    )
    size_parser.add_argument(
        "-r", "--requirements",
        help="Custom requirements (comma-separated)"
    )
    size_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to disk"
    )
    size_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    # ========================================================================
    # LIST command
    # ========================================================================
    list_parser = subparsers.add_parser("list", help="List saved project sizings")
    list_parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Number of results (default: 10)"
    )

    # ========================================================================
    # VIEW command
    # ========================================================================
    view_parser = subparsers.add_parser("view", help="View a saved sizing")
    view_parser.add_argument("sizing_id", help="Sizing ID (e.g., SZ-20251019164530)")
    view_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    # ========================================================================
    # EXPORT command
    # ========================================================================
    export_parser = subparsers.add_parser("export", help="Export sizing to ERPNext")
    export_parser.add_argument("sizing_id", help="Sizing ID to export")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    if args.command == "size":
        return cmd_size(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "view":
        return cmd_view(args)
    elif args.command == "export":
        return cmd_export(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
