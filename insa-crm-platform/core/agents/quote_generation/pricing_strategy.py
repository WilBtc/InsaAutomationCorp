"""
Pricing Strategy Agent
Determines optimal pricing based on costs, competition, and customer value
"""

from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from .config import config

logger = structlog.get_logger()


class PricingStrategyAgent:
    """
    Calculates final pricing strategy for quotes
    Considers costs, markup, competition, and strategic factors
    """

    # Pricing strategies
    STRATEGIES = {
        "cost_plus": "Standard markup on costs",
        "value_based": "Price based on customer value delivered",
        "competitive": "Match or beat competition",
        "penetration": "Low price to win new customer",
        "premium": "High price for complex/unique work",
    }

    def __init__(self):
        """Initialize pricing strategy agent"""
        self.default_markup = config.default_markup_percentage

    def calculate_pricing(
        self,
        bom: Dict[str, Any],
        labor_estimate: Dict[str, Any],
        requirements: Dict[str, Any],
        similar_projects: List[Dict[str, Any]],
        customer_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal pricing strategy

        Args:
            bom: Bill of materials with costs
            labor_estimate: Labor hours and costs
            requirements: Project requirements
            similar_projects: Historical projects
            customer_context: Customer history and preferences

        Returns:
            Pricing strategy dictionary
        """
        try:
            logger.info("Calculating pricing strategy")

            # Base costs
            material_cost = bom.get('summary', {}).get('total_material_cost', 0)
            labor_cost = labor_estimate.get('adjusted_cost', 0)
            total_cost = material_cost + labor_cost

            # Determine strategy
            strategy = self._determine_strategy(
                requirements,
                customer_context,
                similar_projects
            )

            # Calculate markup based on strategy
            markup_percentage = self._calculate_markup(
                strategy,
                requirements,
                customer_context
            )

            # Calculate prices
            markup_amount = total_cost * (markup_percentage / 100)
            subtotal = total_cost + markup_amount

            # Apply strategic adjustments
            adjustments = self._calculate_adjustments(
                subtotal,
                requirements,
                customer_context
            )

            adjusted_total = subtotal
            for adj in adjustments:
                adjusted_total += adj['amount']

            # Calculate payment terms
            payment_terms = self._generate_payment_terms(adjusted_total)

            # Build pricing breakdown
            pricing = {
                "strategy": strategy,
                "costs": {
                    "materials": round(material_cost, 2),
                    "labor": round(labor_cost, 2),
                    "total_cost": round(total_cost, 2),
                },
                "markup": {
                    "percentage": round(markup_percentage, 1),
                    "amount": round(markup_amount, 2),
                    "reasoning": self._explain_markup(strategy, markup_percentage)
                },
                "pricing": {
                    "subtotal": round(subtotal, 2),
                    "adjustments": adjustments,
                    "total": round(adjusted_total, 2),
                    "currency": "USD"
                },
                "payment_terms": payment_terms,
                "validity": {
                    "days": 30,
                    "expiration_date": self._calculate_expiration(30)
                },
                "comparison": self._compare_to_similar_projects(
                    adjusted_total,
                    similar_projects
                ),
                "confidence": self._calculate_pricing_confidence(
                    requirements,
                    customer_context,
                    similar_projects
                ),
                "win_probability": self._estimate_win_probability(
                    adjusted_total,
                    requirements,
                    customer_context
                ),
                "pricing_notes": self._generate_pricing_notes(
                    strategy,
                    requirements,
                    customer_context
                ),
                "calculated_date": datetime.utcnow().isoformat()
            }

            logger.info("Pricing calculated successfully",
                       strategy=strategy,
                       total=adjusted_total,
                       markup=markup_percentage,
                       win_probability=pricing['win_probability'])

            return pricing

        except Exception as e:
            logger.error("Failed to calculate pricing", error=str(e))
            raise

    def _determine_strategy(
        self,
        requirements: Dict[str, Any],
        customer_context: Optional[Dict[str, Any]],
        similar_projects: List[Dict[str, Any]]
    ) -> str:
        """Determine optimal pricing strategy"""

        # New customer? Use penetration pricing
        if not customer_context or customer_context.get('is_new_customer', True):
            return "penetration"

        # High complexity or IEC 62443? Use premium pricing
        complexity = requirements.get('complexity_score', 50)
        standards = requirements.get('compliance_standards', [])

        if complexity >= 80 or any('62443' in str(s) for s in standards):
            return "premium"

        # Budget-sensitive customer? Use competitive pricing
        if customer_context and customer_context.get('price_sensitive', False):
            return "competitive"

        # Strategic customer? Use value-based pricing
        if customer_context and customer_context.get('strategic_importance', 0) > 7:
            return "value_based"

        # Default: cost-plus
        return "cost_plus"

    def _calculate_markup(
        self,
        strategy: str,
        requirements: Dict[str, Any],
        customer_context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate markup percentage based on strategy"""

        complexity = requirements.get('complexity_score', 50)

        markup_map = {
            "cost_plus": 30.0,  # Standard 30%
            "value_based": 35.0 + (complexity / 10),  # 35-45% based on complexity
            "competitive": 25.0,  # Lower margin to compete
            "penetration": 20.0,  # Minimal margin to win new customer
            "premium": 40.0 + (complexity / 10),  # 40-50% for complex work
        }

        base_markup = markup_map.get(strategy, self.default_markup)

        # Adjust for risk factors
        missing_info = requirements.get('missing_information', [])
        if len(missing_info) > 3:
            base_markup += 5.0  # Add 5% for uncertainty

        # Adjust for IEC 62443 compliance (higher value)
        standards = requirements.get('compliance_standards', [])
        if any('62443' in str(s) for s in standards):
            base_markup += 5.0

        return round(base_markup, 1)

    def _calculate_adjustments(
        self,
        subtotal: float,
        requirements: Dict[str, Any],
        customer_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate pricing adjustments"""
        adjustments = []

        # Discount for repeat customer
        if customer_context and customer_context.get('project_count', 0) >= 3:
            discount_pct = min(5.0, customer_context.get('project_count', 0))  # Max 5%
            discount_amount = -(subtotal * discount_pct / 100)
            adjustments.append({
                "description": f"Repeat Customer Discount ({discount_pct}%)",
                "amount": round(discount_amount, 2),
                "type": "discount"
            })

        # Risk premium for tight timeline
        timeline = requirements.get('project_timeline', {})
        duration_months = timeline.get('duration_months', 6)
        if duration_months < 3:
            rush_fee = subtotal * 0.10  # 10% rush fee
            adjustments.append({
                "description": "Expedited Delivery (10%)",
                "amount": round(rush_fee, 2),
                "type": "premium"
            })

        # Hazardous location premium
        site_info = requirements.get('site_information', {})
        if 'hazard' in site_info.get('environment', '').lower():
            hazloc_fee = subtotal * 0.05  # 5% hazloc fee
            adjustments.append({
                "description": "Hazardous Location Premium (5%)",
                "amount": round(hazloc_fee, 2),
                "type": "premium"
            })

        return adjustments

    def _generate_payment_terms(self, total: float) -> Dict[str, Any]:
        """Generate payment schedule"""

        # Standard terms: 30% upfront, 40% mid-project, 30% completion
        return {
            "schedule": [
                {
                    "milestone": "Contract Signing",
                    "percentage": 30,
                    "amount": round(total * 0.30, 2),
                    "due_date": "Upon contract execution"
                },
                {
                    "milestone": "Design Approval / FAT",
                    "percentage": 40,
                    "amount": round(total * 0.40, 2),
                    "due_date": "Midpoint of project"
                },
                {
                    "milestone": "Successful SAT / Completion",
                    "percentage": 30,
                    "amount": round(total * 0.30, 2),
                    "due_date": "Upon acceptance"
                }
            ],
            "terms": "Net 15 days",
            "late_fee": "1.5% per month on overdue balances"
        }

    def _calculate_expiration(self, days: int) -> str:
        """Calculate quote expiration date"""
        from datetime import timedelta
        expiration = datetime.utcnow() + timedelta(days=days)
        return expiration.strftime('%Y-%m-%d')

    def _compare_to_similar_projects(
        self,
        quoted_price: float,
        similar_projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare price to similar historical projects"""

        if not similar_projects or len(similar_projects) == 0:
            return {
                "comparison_available": False,
                "note": "No similar historical projects for comparison"
            }

        # Extract prices from similar projects (if available)
        # For now, return placeholder
        return {
            "comparison_available": True,
            "similar_project_count": len(similar_projects),
            "note": f"Pricing aligned with {len(similar_projects)} similar past projects"
        }

    def _calculate_pricing_confidence(
        self,
        requirements: Dict[str, Any],
        customer_context: Optional[Dict[str, Any]],
        similar_projects: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in pricing accuracy"""

        confidence = 0.6  # Base confidence

        # Increase if requirements are clear
        req_confidence = requirements.get('confidence_score', 0.5)
        confidence += req_confidence * 0.2

        # Increase if we have customer history
        if customer_context and customer_context.get('project_count', 0) > 0:
            confidence += 0.1

        # Increase if we have similar projects
        if similar_projects and len(similar_projects) > 0:
            confidence += 0.1

        return min(confidence, 1.0)

    def _estimate_win_probability(
        self,
        quoted_price: float,
        requirements: Dict[str, Any],
        customer_context: Optional[Dict[str, Any]]
    ) -> float:
        """Estimate probability of winning this quote"""

        # Base probability
        win_prob = 0.30  # 30% base win rate

        # Increase for repeat customers
        if customer_context and customer_context.get('project_count', 0) > 0:
            win_prob += 0.20  # +20% for existing customers

        # Increase for high-fit projects
        industry_fit = requirements.get('industry', '')
        if industry_fit in ['Oil & Gas', 'Manufacturing', 'Utilities']:
            win_prob += 0.15  # +15% for core industries

        # Increase for IEC 62443 (our specialty)
        standards = requirements.get('compliance_standards', [])
        if any('62443' in str(s) for s in standards):
            win_prob += 0.20  # +20% for our differentiator

        # Decrease for very high quotes
        budget = requirements.get('budget', {}).get('stated_budget', 0)
        if budget > 0 and quoted_price > budget * 1.2:
            win_prob -= 0.15  # -15% if 20%+ over budget

        return min(max(win_prob, 0.10), 0.90)  # Clamp between 10-90%

    def _explain_markup(self, strategy: str, markup: float) -> str:
        """Explain markup reasoning"""

        explanations = {
            "cost_plus": f"Standard {markup}% markup on total project costs",
            "value_based": f"{markup}% markup reflecting high value delivered to customer",
            "competitive": f"{markup}% competitive pricing to win against alternatives",
            "penetration": f"{markup}% introductory pricing for new customer relationship",
            "premium": f"{markup}% premium pricing for complex/specialized work",
        }

        return explanations.get(strategy, f"{markup}% markup applied")

    def _generate_pricing_notes(
        self,
        strategy: str,
        requirements: Dict[str, Any],
        customer_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate notes about pricing decisions"""

        notes = [
            f"Pricing strategy: {strategy}",
            "All costs based on current market rates",
            "Quote valid for 30 days from date of issue",
        ]

        # Add strategy-specific notes
        if strategy == "penetration":
            notes.append("Competitive pricing offered to establish partnership")

        if strategy == "premium":
            notes.append("Premium pricing reflects specialized expertise and compliance requirements")

        # Add risk notes
        missing_info = requirements.get('missing_information', [])
        if len(missing_info) > 2:
            notes.append("Price may be refined as additional requirements are clarified")

        return notes
