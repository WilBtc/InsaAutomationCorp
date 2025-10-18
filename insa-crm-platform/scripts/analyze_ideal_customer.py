#!/usr/bin/env python3
"""
INSA CRM Platform - Ideal Customer Profile Analyzer
Analyzes historical deal data to optimize lead scoring weights

This script analyzes win/loss patterns to identify:
1. Ideal budget range
2. Most profitable industries
3. Best-fit company sizes
4. Geographic preferences
5. Decision-maker profiles

Output: INSA-specific scoring weights for lead_qualification_agent.py

Usage:
    python3 analyze_ideal_customer.py historical_deals.csv

Expected CSV format:
    customer_name, industry, budget, company_size, geography, won, margin, close_time_days

Author: INSA Automation Corp
Date: October 18, 2025
"""

import sys
import csv
import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from statistics import mean, median


class IdealCustomerAnalyzer:
    """Analyzes historical data to identify INSA's ideal customer profile"""

    def __init__(self):
        self.deals = []
        self.won_deals = []
        self.lost_deals = []
        self.analysis = {}

    def load_deals(self, csv_path: Path) -> None:
        """Load historical deals from CSV"""
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                deal = {
                    'customer_name': row['customer_name'],
                    'industry': row['industry'],
                    'budget': float(row.get('budget', 0)),
                    'company_size': row.get('company_size', 'unknown'),
                    'geography': row.get('geography', 'unknown'),
                    'won': row['won'].lower() in ['true', '1', 'yes'],
                    'margin': float(row.get('margin', 0)),
                    'close_time_days': int(row.get('close_time_days', 0))
                }
                self.deals.append(deal)

                if deal['won']:
                    self.won_deals.append(deal)
                else:
                    self.lost_deals.append(deal)

        print(f"✓ Loaded {len(self.deals)} deals")
        print(f"  - Won: {len(self.won_deals)}")
        print(f"  - Lost: {len(self.lost_deals)}")
        print(f"  - Win Rate: {len(self.won_deals)/len(self.deals)*100:.1f}%")

    def analyze_budget_range(self) -> Dict[str, Any]:
        """Analyze ideal budget range"""
        if not self.won_deals:
            return {}

        budgets = [d['budget'] for d in self.won_deals if d['budget'] > 0]

        if not budgets:
            return {}

        # Calculate percentiles
        budgets_sorted = sorted(budgets)
        p10 = budgets_sorted[int(len(budgets) * 0.1)]
        p25 = budgets_sorted[int(len(budgets) * 0.25)]
        p50 = median(budgets)
        p75 = budgets_sorted[int(len(budgets) * 0.75)]
        p90 = budgets_sorted[int(len(budgets) * 0.9)]

        # Identify sweet spot (highest win rate + margin)
        budget_ranges = {
            'under_50k': [d for d in self.won_deals if d['budget'] < 50000],
            '50k_100k': [d for d in self.won_deals if 50000 <= d['budget'] < 100000],
            '100k_250k': [d for d in self.won_deals if 100000 <= d['budget'] < 250000],
            '250k_500k': [d for d in self.won_deals if 250000 <= d['budget'] < 500000],
            'over_500k': [d for d in self.won_deals if d['budget'] >= 500000],
        }

        # Calculate avg margin by range
        range_margins = {}
        for range_name, deals in budget_ranges.items():
            if deals:
                avg_margin = mean([d['margin'] for d in deals])
                range_margins[range_name] = {
                    'count': len(deals),
                    'avg_margin': avg_margin
                }

        return {
            'min': min(budgets),
            'max': max(budgets),
            'mean': mean(budgets),
            'median': p50,
            'p25': p25,
            'p75': p75,
            'p10': p10,
            'p90': p90,
            'sweet_spot_range': (p25, p75),
            'by_range': range_margins
        }

    def analyze_industries(self) -> Dict[str, Any]:
        """Analyze best-performing industries"""
        # Group deals by industry
        by_industry = defaultdict(lambda: {'won': 0, 'lost': 0, 'margins': []})

        for deal in self.deals:
            industry = deal['industry']
            if deal['won']:
                by_industry[industry]['won'] += 1
                by_industry[industry]['margins'].append(deal['margin'])
            else:
                by_industry[industry]['lost'] += 1

        # Calculate win rates and avg margins
        industry_analysis = {}
        for industry, stats in by_industry.items():
            total = stats['won'] + stats['lost']
            win_rate = (stats['won'] / total) * 100 if total > 0 else 0
            avg_margin = mean(stats['margins']) if stats['margins'] else 0

            industry_analysis[industry] = {
                'total_deals': total,
                'won': stats['won'],
                'lost': stats['lost'],
                'win_rate': win_rate,
                'avg_margin': avg_margin,
                'score': win_rate * 0.6 + avg_margin * 0.4  # Combined score
            }

        # Sort by combined score
        sorted_industries = sorted(
            industry_analysis.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )

        return {
            'top_3': [ind[0] for ind in sorted_industries[:3]],
            'details': dict(sorted_industries)
        }

    def analyze_company_size(self) -> Dict[str, Any]:
        """Analyze ideal company size"""
        by_size = defaultdict(lambda: {'won': 0, 'lost': 0, 'margins': []})

        for deal in self.deals:
            size = deal['company_size']
            if deal['won']:
                by_size[size]['won'] += 1
                by_size[size]['margins'].append(deal['margin'])
            else:
                by_size[size]['lost'] += 1

        # Calculate win rates
        size_analysis = {}
        for size, stats in by_size.items():
            total = stats['won'] + stats['lost']
            win_rate = (stats['won'] / total) * 100 if total > 0 else 0
            avg_margin = mean(stats['margins']) if stats['margins'] else 0

            size_analysis[size] = {
                'total_deals': total,
                'won': stats['won'],
                'win_rate': win_rate,
                'avg_margin': avg_margin
            }

        return size_analysis

    def analyze_geography(self) -> Dict[str, Any]:
        """Analyze geographic win patterns"""
        by_geo = defaultdict(lambda: {'won': 0, 'lost': 0})

        for deal in self.deals:
            geo = deal['geography']
            if deal['won']:
                by_geo[geo]['won'] += 1
            else:
                by_geo[geo]['lost'] += 1

        # Calculate win rates
        geo_analysis = {}
        for geo, stats in by_geo.items():
            total = stats['won'] + stats['lost']
            win_rate = (stats['won'] / total) * 100 if total > 0 else 0

            geo_analysis[geo] = {
                'total_deals': total,
                'won': stats['won'],
                'win_rate': win_rate
            }

        return geo_analysis

    def generate_scoring_weights(self) -> Dict[str, Any]:
        """Generate INSA-specific lead scoring weights"""
        budget_analysis = self.analyze_budget_range()
        industry_analysis = self.analyze_industries()
        size_analysis = self.analyze_company_size()
        geo_analysis = self.analyze_geography()

        # Store full analysis
        self.analysis = {
            'budget': budget_analysis,
            'industries': industry_analysis,
            'company_size': size_analysis,
            'geography': geo_analysis
        }

        # Generate weights for lead_qualification_agent.py
        weights = {
            'budget': {
                'weight': 0.30,
                'ideal_range': budget_analysis.get('sweet_spot_range', (50000, 500000)),
                'minimum': budget_analysis.get('p10', 20000),
                'comment': f"Based on {len(self.won_deals)} won deals, median: ${budget_analysis.get('median', 0):,.0f}"
            },
            'industry': {
                'weight': 0.25,
                'preferred': industry_analysis.get('top_3', []),
                'bonus_points': 15,
                'comment': f"Top 3 industries by win rate + margin"
            },
            'company_size': {
                'weight': 0.15,
                'preferred': self._get_top_sizes(size_analysis),
                'comment': "Based on historical win rates"
            },
            'geography': {
                'weight': 0.10,
                'preferred': self._get_top_geos(geo_analysis),
                'comment': "Based on historical win rates"
            },
            'decision_maker': {
                'weight': 0.20,
                'preferred_titles': ['VP Engineering', 'Plant Manager', 'Operations Director'],
                'comment': "INSA typical buyer personas"
            }
        }

        return weights

    def _get_top_sizes(self, size_analysis: Dict) -> List[str]:
        """Get top company sizes by win rate"""
        sorted_sizes = sorted(
            size_analysis.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )
        return [s[0] for s in sorted_sizes[:3]]

    def _get_top_geos(self, geo_analysis: Dict) -> List[str]:
        """Get top geographies by win rate"""
        sorted_geos = sorted(
            geo_analysis.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )
        return [g[0] for g in sorted_geos[:3]]

    def print_report(self) -> None:
        """Print comprehensive analysis report"""
        print(f"\n{'='*80}")
        print(f"INSA IDEAL CUSTOMER PROFILE ANALYSIS")
        print(f"{'='*80}\n")

        # Budget analysis
        budget = self.analysis.get('budget', {})
        if budget:
            print("BUDGET ANALYSIS:")
            print(f"  Sweet Spot Range: ${budget['sweet_spot_range'][0]:,.0f} - ${budget['sweet_spot_range'][1]:,.0f}")
            print(f"  Median Won Deal: ${budget['median']:,.0f}")
            print(f"  Mean Won Deal: ${budget['mean']:,.0f}")
            print(f"  Min/Max: ${budget['min']:,.0f} / ${budget['max']:,.0f}")
            print("")

            print("  By Range:")
            for range_name, stats in budget.get('by_range', {}).items():
                print(f"    {range_name}: {stats['count']} deals, {stats['avg_margin']:.1f}% avg margin")
            print("")

        # Industry analysis
        industries = self.analysis.get('industries', {})
        if industries:
            print("INDUSTRY ANALYSIS:")
            print(f"  Top 3 Industries: {', '.join(industries.get('top_3', []))}")
            print("")
            print("  Detailed Breakdown:")
            for industry, stats in industries.get('details', {}).items():
                print(f"    {industry}:")
                print(f"      Win Rate: {stats['win_rate']:.1f}%")
                print(f"      Avg Margin: {stats['avg_margin']:.1f}%")
                print(f"      Total Deals: {stats['total_deals']}")
            print("")

        # Company size
        sizes = self.analysis.get('company_size', {})
        if sizes:
            print("COMPANY SIZE ANALYSIS:")
            for size, stats in sizes.items():
                print(f"  {size}: {stats['win_rate']:.1f}% win rate ({stats['won']} won)")
            print("")

        # Geography
        geos = self.analysis.get('geography', {})
        if geos:
            print("GEOGRAPHY ANALYSIS:")
            for geo, stats in geos.items():
                print(f"  {geo}: {stats['win_rate']:.1f}% win rate ({stats['won']} won)")
            print("")

    def save_weights(self, output_path: Path) -> None:
        """Save scoring weights to JSON file"""
        weights = self.generate_scoring_weights()

        with open(output_path, 'w') as f:
            json.dump(weights, f, indent=2)

        print(f"✅ Scoring weights saved to: {output_path}")
        print("")
        print("To use these weights, update:")
        print("  ~/insa-crm-platform/core/agents/lead_qualification_agent.py")
        print("")
        print("Replace SCORING_WEIGHTS with the generated configuration.")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_ideal_customer.py <historical_deals.csv>")
        print("")
        print("Example:")
        print("  python3 analyze_ideal_customer.py /var/lib/insa-crm/historical_deals.csv")
        print("")
        print("CSV Format:")
        print("  customer_name, industry, budget, company_size, geography, won, margin, close_time_days")
        sys.exit(1)

    csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)

    # Analyze
    analyzer = IdealCustomerAnalyzer()
    analyzer.load_deals(csv_path)
    analyzer.print_report()

    # Save weights
    output_path = Path('/tmp/insa_scoring_weights.json')
    analyzer.save_weights(output_path)


if __name__ == '__main__':
    main()
