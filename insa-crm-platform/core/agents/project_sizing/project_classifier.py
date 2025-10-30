"""
Project Classifier - AI-powered project type identification
Classifies projects into INSA taxonomy and determines complexity
"""

import re
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from config import (
    PROJECT_TYPES,
    COMPLEXITY_FACTORS,
    STANDARDS_BY_COUNTRY,
    INSA_DISCIPLINES,
    AI_MODEL,
    AI_TIMEOUT_SECONDS
)


class ProjectClassifier:
    """
    AI-powered project classification system

    Identifies:
    - Project type (separator, compressor, tank farm, etc)
    - Project variant (three-phase separator, gas compressor, etc)
    - Complexity level (basic, standard, advanced, custom)
    - Required disciplines
    - Applicable complexity factors
    - Country-specific standards
    """

    def __init__(self):
        self.project_types = PROJECT_TYPES
        self.complexity_factors = COMPLEXITY_FACTORS
        self.standards = STANDARDS_BY_COUNTRY

    def classify(
        self,
        project_description: str,
        customer_name: Optional[str] = None,
        country: str = "colombia",
        additional_context: Optional[Dict] = None
    ) -> Dict:
        """
        Classify a project based on description

        Args:
            project_description: Natural language project description
            customer_name: Customer name (for repeat project detection)
            country: Project country (colombia/ecuador/usa)
            additional_context: Optional additional context (budget, timeline, etc)

        Returns:
            Classification result with confidence scores
        """

        # Step 1: Rule-based classification (fast, deterministic)
        rule_based_result = self._rule_based_classification(project_description)

        # Step 2: AI-powered classification (slower, more accurate)
        ai_result = self._ai_classification(
            project_description,
            customer_name,
            country,
            additional_context
        )

        # Step 3: Merge results (AI takes precedence if confidence > 0.8)
        final_result = self._merge_classifications(rule_based_result, ai_result)

        # Step 4: Identify complexity factors
        final_result["complexity_factors"] = self._identify_complexity_factors(
            project_description,
            customer_name,
            final_result
        )

        # Step 5: Determine required disciplines
        final_result["required_disciplines"] = self._determine_disciplines(
            final_result["project_type"],
            final_result["complexity_factors"]
        )

        # Step 6: Apply country-specific standards
        final_result["applicable_standards"] = self.standards.get(country, self.standards["colombia"])

        # Step 7: Calculate overall confidence
        final_result["overall_confidence"] = self._calculate_confidence(final_result)

        return final_result

    def _rule_based_classification(self, description: str) -> Dict:
        """
        Fast rule-based classification using keywords
        """
        description_lower = description.lower()

        # Keyword matching for project types
        type_scores = {}

        for project_type, config in self.project_types.items():
            score = 0

            # Match project name
            if project_type in description_lower:
                score += 10

            # Match variants
            for variant in config.get("variants", []):
                variant_words = variant.replace("_", " ")
                if variant_words in description_lower:
                    score += 5

            type_scores[project_type] = score

        # Get best match
        if max(type_scores.values()) == 0:
            best_type = "custom"
            confidence = 0.3
        else:
            best_type = max(type_scores, key=type_scores.get)
            confidence = min(type_scores[best_type] / 15, 0.9)  # Cap at 0.9

        # Determine complexity keywords
        complexity = "standard"
        if any(word in description_lower for word in ["basic", "simple", "small", "single"]):
            complexity = "basic"
        elif any(word in description_lower for word in ["advanced", "complex", "large", "multi"]):
            complexity = "advanced"
        elif any(word in description_lower for word in ["custom", "special", "unique"]):
            complexity = "custom"

        return {
            "project_type": best_type,
            "complexity": complexity,
            "confidence": confidence,
            "method": "rule_based"
        }

    def _ai_classification(
        self,
        description: str,
        customer_name: Optional[str],
        country: str,
        context: Optional[Dict]
    ) -> Dict:
        """
        AI-powered classification using Claude Code subprocess

        Uses local Claude Code (zero API cost) to analyze project
        """

        # Build AI prompt
        prompt = self._build_classification_prompt(description, customer_name, country, context)

        try:
            # Call Claude Code via subprocess (zero cost!)
            result = subprocess.run(
                ["claude", "code", "--prompt", prompt, "--json"],
                capture_output=True,
                text=True,
                timeout=AI_TIMEOUT_SECONDS
            )

            if result.returncode == 0:
                ai_response = json.loads(result.stdout)

                return {
                    "project_type": ai_response.get("project_type", "unknown"),
                    "variant": ai_response.get("variant"),
                    "complexity": ai_response.get("complexity", "standard"),
                    "confidence": ai_response.get("confidence", 0.7),
                    "reasoning": ai_response.get("reasoning", ""),
                    "method": "ai_powered"
                }
            else:
                # AI failed, return low confidence
                return {"confidence": 0.0, "method": "ai_failed"}

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            # Fallback to rule-based only
            return {"confidence": 0.0, "method": "ai_error", "error": str(e)}

    def _build_classification_prompt(
        self,
        description: str,
        customer_name: Optional[str],
        country: str,
        context: Optional[Dict]
    ) -> str:
        """
        Build AI prompt for project classification
        """

        project_types_list = "\n".join([
            f"- {ptype}: {config['name']} (variants: {', '.join(config['variants'])})"
            for ptype, config in self.project_types.items()
        ])

        prompt = f"""
You are an industrial automation project classification expert for INSA Automation Corp.

Classify this project into INSA's taxonomy:

**Project Description:**
{description}

**Customer:** {customer_name or "Unknown"}
**Country:** {country}
**Additional Context:** {json.dumps(context) if context else "None"}

**Available Project Types:**
{project_types_list}

**Complexity Levels:**
- basic: Simple, single-discipline, small scope
- standard: Typical project, 2-4 disciplines, moderate scope
- advanced: Complex, multi-discipline, large scope or advanced tech
- custom: Unique/specialized requirements, R&D component

**Output Format (JSON):**
{{
  "project_type": "separator|compressor|tank_farm|metering|pipeline|wellhead|scada|panel",
  "variant": "specific variant from the list above",
  "complexity": "basic|standard|advanced|custom",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of classification"
}}

Analyze the project and provide classification.
"""
        return prompt

    def _merge_classifications(self, rule_result: Dict, ai_result: Dict) -> Dict:
        """
        Merge rule-based and AI classifications
        AI takes precedence if confidence > 0.8
        """

        ai_confidence = ai_result.get("confidence", 0.0)
        rule_confidence = rule_result.get("confidence", 0.0)

        if ai_confidence > 0.8:
            # Trust AI
            return {
                "project_type": ai_result["project_type"],
                "variant": ai_result.get("variant"),
                "complexity": ai_result["complexity"],
                "classification_method": "ai_primary",
                "ai_confidence": ai_confidence,
                "rule_confidence": rule_confidence,
                "ai_reasoning": ai_result.get("reasoning", "")
            }
        elif rule_confidence > 0.7:
            # Trust rules
            return {
                "project_type": rule_result["project_type"],
                "variant": None,
                "complexity": rule_result["complexity"],
                "classification_method": "rule_primary",
                "ai_confidence": ai_confidence,
                "rule_confidence": rule_confidence
            }
        else:
            # Low confidence - combine both
            return {
                "project_type": ai_result.get("project_type", rule_result["project_type"]),
                "variant": ai_result.get("variant"),
                "complexity": ai_result.get("complexity", rule_result["complexity"]),
                "classification_method": "hybrid_low_confidence",
                "ai_confidence": ai_confidence,
                "rule_confidence": rule_confidence,
                "warning": "Low confidence classification - requires manual review"
            }

    def _identify_complexity_factors(
        self,
        description: str,
        customer_name: Optional[str],
        classification: Dict
    ) -> List[str]:
        """
        Identify applicable complexity factors based on project description
        """

        description_lower = description.lower()
        applicable_factors = []

        # Check each complexity factor
        for factor_key, factor_config in self.complexity_factors.items():
            # Keyword matching
            if factor_key == "hazardous_area":
                if any(word in description_lower for word in ["hazardous", "atex", "iecex", "zone 1", "division 1", "explosive"]):
                    applicable_factors.append(factor_key)

            elif factor_key == "cybersecurity_required":
                if any(word in description_lower for word in ["cybersecurity", "iec 62443", "cyber", "security"]):
                    applicable_factors.append(factor_key)

            elif factor_key == "scada_integration":
                if any(word in description_lower for word in ["scada", "dcs", "hmi", "remote monitoring"]):
                    applicable_factors.append(factor_key)

            elif factor_key == "sil_rated":
                if any(word in description_lower for word in ["sil", "safety instrumented", "sis"]):
                    applicable_factors.append(factor_key)

            elif factor_key == "offshore":
                if any(word in description_lower for word in ["offshore", "platform", "subsea"]):
                    applicable_factors.append(factor_key)

            elif factor_key == "fast_track":
                if any(word in description_lower for word in ["fast track", "urgent", "accelerated", "rush"]):
                    applicable_factors.append(factor_key)

            elif factor_key == "new_customer":
                # Check if customer is in our database (future: query ERPNext)
                if customer_name and customer_name.lower() not in ["deilim", "ecopetrol", "conocophillips"]:
                    applicable_factors.append(factor_key)

            elif factor_key == "repeat_project":
                if any(word in description_lower for word in ["similar to", "repeat", "duplicate", "like previous"]):
                    applicable_factors.append(factor_key)

        return applicable_factors

    def _determine_disciplines(self, project_type: str, complexity_factors: List[str]) -> List[str]:
        """
        Determine required disciplines based on project type and complexity
        """

        # Start with typical disciplines for project type
        base_disciplines = self.project_types.get(project_type, {}).get("typical_disciplines", [])
        required_disciplines = list(base_disciplines)

        # Add disciplines based on complexity factors
        if "cybersecurity_required" in complexity_factors:
            if "cybersecurity" not in required_disciplines:
                required_disciplines.append("cybersecurity")

        if "scada_integration" in complexity_factors:
            if "digitalization" not in required_disciplines:
                required_disciplines.append("digitalization")

        if "sil_rated" in complexity_factors:
            if "quality" not in required_disciplines:
                required_disciplines.append("quality")

        # Always include quality for standard+ projects
        if "quality" not in required_disciplines:
            required_disciplines.append("quality")

        return required_disciplines

    def _calculate_confidence(self, classification: Dict) -> float:
        """
        Calculate overall confidence score for classification
        """

        method = classification.get("classification_method", "unknown")
        ai_conf = classification.get("ai_confidence", 0.0)
        rule_conf = classification.get("rule_confidence", 0.0)

        if method == "ai_primary":
            return ai_conf
        elif method == "rule_primary":
            return rule_conf
        else:
            # Hybrid - average but penalize
            return (ai_conf + rule_conf) / 2 * 0.85

    def get_classification_summary(self, classification: Dict) -> str:
        """
        Generate human-readable classification summary
        """

        project_type_name = self.project_types.get(
            classification["project_type"],
            {}
        ).get("name", "Unknown Project Type")

        summary = f"""
Project Classification Summary
{'='*60}

Project Type: {project_type_name}
Variant: {classification.get('variant', 'Not specified')}
Complexity: {classification['complexity'].upper()}
Overall Confidence: {classification['overall_confidence']:.1%}

Required Disciplines ({len(classification['required_disciplines'])}):
"""
        for disc in classification['required_disciplines']:
            disc_name = INSA_DISCIPLINES.get(disc, {}).get("name", disc)
            summary += f"  - {disc_name}\n"

        if classification.get("complexity_factors"):
            summary += f"\nComplexity Factors ({len(classification['complexity_factors'])}):\n"
            for factor in classification['complexity_factors']:
                factor_desc = self.complexity_factors[factor]["description"]
                multiplier = self.complexity_factors[factor]["multiplier"]
                summary += f"  - {factor_desc} (×{multiplier})\n"

        if classification.get("ai_reasoning"):
            summary += f"\nAI Reasoning:\n{classification['ai_reasoning']}\n"

        if classification.get("warning"):
            summary += f"\n⚠️  WARNING: {classification['warning']}\n"

        return summary


# ============================================================================
# CLI Testing Interface
# ============================================================================

if __name__ == "__main__":
    import sys

    # Test classification
    classifier = ProjectClassifier()

    test_description = """
    Three-phase test separator for PAD-3 location.
    Requirements include PLC control system (Allen-Bradley),
    HMI/SCADA integration, instrumentation (level, pressure, temperature sensors),
    electrical panel design. Project located in Colombia, must comply with RETIE.
    Timeline is urgent - need completion in 4 months.
    """

    print("Testing Project Classifier...")
    print(f"Description: {test_description[:100]}...\n")

    result = classifier.classify(
        project_description=test_description,
        customer_name="Deilim Colombia",
        country="colombia"
    )

    print(classifier.get_classification_summary(result))
    print(f"\nFull Classification Result:")
    print(json.dumps(result, indent=2))
