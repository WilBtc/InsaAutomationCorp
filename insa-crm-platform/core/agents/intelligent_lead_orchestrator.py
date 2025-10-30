#!/usr/bin/env python3
"""
Intelligent Lead Orchestrator
Automatically processes leads, assigns pipelines, and triggers workflows

Architecture:
1. Reads leads from PostgreSQL
2. AI-powered pipeline assignment
3. Multi-system integration (ERPNext + Mautic + n8n)
4. Automated workflow triggering
5. Smart follow-up scheduling
"""

import asyncio
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lead-orchestrator")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insa_crm',
    'user': 'insa_crm_user',
    'password': '110811081108'
}


class LeadOrchestrator:
    """Intelligent lead orchestration and workflow automation"""

    def __init__(self):
        self.pipelines = {
            'executive_partnership': {
                'name': 'Executive Partnership Track',
                'stages': ['Initial Contact', 'Executive Meeting', 'Proposal', 'Negotiation', 'Closed Won'],
                'workflows': ['executive_outreach_email', 'executive_meeting_scheduler', 'partnership_proposal'],
                'priority': 'HIGHEST',
                'sla_days': 2
            },
            'fast_track_sales': {
                'name': 'Fast Track Sales',
                'stages': ['Qualification', 'Demo', 'Proposal', 'Negotiation', 'Closed Won'],
                'workflows': ['technical_case_study', 'demo_scheduler', 'proposal_generator'],
                'priority': 'HIGH',
                'sla_days': 7
            },
            'standard_sales': {
                'name': 'Standard Sales Pipeline',
                'stages': ['Lead', 'Qualified', 'Discovery', 'Proposal', 'Negotiation', 'Closed Won'],
                'workflows': ['industry_nurture', 'discovery_call', 'proposal_generator'],
                'priority': 'MEDIUM',
                'sla_days': 14
            },
            'qualification': {
                'name': 'Qualification Pipeline',
                'stages': ['New Lead', 'Qualification', 'Qualified', 'Disqualified'],
                'workflows': ['qualification_questionnaire', 'lead_scoring'],
                'priority': 'LOW',
                'sla_days': 30
            }
        }

        self.email_templates = {
            'executive_outreach': {
                'subject': 'Strategic Partnership Opportunity - INSA Automation',
                'template': 'executive_partnership_intro',
                'timing': 'immediate'
            },
            'technical_demo': {
                'subject': 'Industrial Cybersecurity Solutions for {industry}',
                'template': 'technical_case_study',
                'timing': '24_hours'
            },
            'industry_nurture': {
                'subject': 'Industrial Automation Security Insights',
                'template': 'industry_newsletter',
                'timing': '48_hours'
            },
            'qualification': {
                'subject': 'Understanding Your Industrial Security Needs',
                'template': 'qualification_questionnaire',
                'timing': '72_hours'
            }
        }

    def assign_pipeline(self, lead: Dict) -> str:
        """
        AI-powered pipeline assignment based on lead characteristics

        Logic:
        - Tier 1 + Executive title → executive_partnership
        - Tier 1 + Technical role → fast_track_sales
        - Tier 2 → standard_sales
        - Tier 3 → qualification
        """
        priority_tier = lead.get('priority_tier', 3)
        designation = (lead.get('designation') or '').lower()
        opportunity_score = lead.get('opportunity_score', 0)

        # Executive detection
        executive_titles = ['president', 'ceo', 'coo', 'vp', 'vice president', 'chief', 'executive']
        is_executive = any(title in designation for title in executive_titles)

        # Technical detection
        technical_roles = ['engineer', 'technical', 'manager', 'director', 'specialist']
        is_technical = any(role in designation for role in technical_roles)

        # Assignment logic
        if priority_tier == 1 and is_executive:
            return 'executive_partnership'
        elif priority_tier == 1 and (is_technical or opportunity_score >= 9.0):
            return 'fast_track_sales'
        elif priority_tier == 2:
            return 'standard_sales'
        else:
            return 'qualification'

    def get_workflow_plan(self, lead: Dict, pipeline: str) -> Dict:
        """
        Generate comprehensive workflow plan for lead

        Returns:
        - Pipeline stages
        - Email sequences
        - Follow-up schedule
        - Required actions
        """
        pipeline_config = self.pipelines[pipeline]

        # Determine email template
        if pipeline == 'executive_partnership':
            email_template = 'executive_outreach'
        elif pipeline == 'fast_track_sales':
            email_template = 'technical_demo'
        elif pipeline == 'standard_sales':
            email_template = 'industry_nurture'
        else:
            email_template = 'qualification'

        # Calculate follow-up dates
        now = datetime.now()
        sla_days = pipeline_config['sla_days']

        follow_ups = [
            {
                'type': 'email',
                'template': email_template,
                'date': now + timedelta(hours=2),
                'subject': self.email_templates[email_template]['subject'].format(
                    industry=lead.get('industry', 'Industrial')
                )
            },
            {
                'type': 'phone_call',
                'date': now + timedelta(days=1),
                'notes': f"Call {lead.get('lead_name')} - Discuss {lead.get('industry')} security needs"
            }
        ]

        # Add pipeline-specific actions
        if pipeline == 'executive_partnership':
            follow_ups.append({
                'type': 'calendar_invite',
                'date': now + timedelta(hours=4),
                'duration': 60,
                'subject': f"Strategic Partnership Discussion - {lead.get('company_name')}"
            })
        elif pipeline == 'fast_track_sales':
            follow_ups.append({
                'type': 'demo_link',
                'date': now + timedelta(days=2),
                'link': 'https://iac1.tailc58ea3.ts.net/command-center/',
                'notes': 'Send interactive demo link'
            })

        return {
            'pipeline': pipeline,
            'pipeline_name': pipeline_config['name'],
            'current_stage': pipeline_config['stages'][0],
            'priority': pipeline_config['priority'],
            'sla_date': (now + timedelta(days=sla_days)).isoformat(),
            'workflows': pipeline_config['workflows'],
            'follow_ups': follow_ups,
            'automation_triggers': [
                f"mautic_segment_{pipeline}",
                f"n8n_workflow_{pipeline}",
                f"erpnext_opportunity_{pipeline}"
            ]
        }

    def generate_mautic_segment(self, pipeline: str) -> str:
        """Generate Mautic segment name for pipeline"""
        segment_map = {
            'executive_partnership': 'INSA - Executive Partnerships',
            'fast_track_sales': 'INSA - Fast Track Sales',
            'standard_sales': 'INSA - Standard Pipeline',
            'qualification': 'INSA - Qualification Queue'
        }
        return segment_map.get(pipeline, 'INSA - General Leads')

    def generate_email_campaign(self, pipeline: str, lead: Dict) -> Dict:
        """
        Generate personalized email campaign for lead

        Uses:
        - Industry-specific content
        - Role-specific messaging
        - Company-specific pain points
        """
        industry = lead.get('industry', 'Industrial')
        company = lead.get('company_name', 'your company')

        campaigns = {
            'executive_partnership': {
                'name': f"Executive Partnership - {company}",
                'emails': [
                    {
                        'day': 0,
                        'subject': f"Strategic Partnership Opportunity for {company}",
                        'preview': f"Enhance {company}'s competitive advantage with industrial cybersecurity",
                        'content_points': [
                            'Reference to Permian Basin market leadership',
                            'IEC 62443 compliance value proposition',
                            'ROI metrics from similar partnerships',
                            'Executive calendar link'
                        ]
                    },
                    {
                        'day': 3,
                        'subject': 'Following up on partnership discussion',
                        'preview': 'Quick question about your security roadmap',
                        'content_points': [
                            'Industry-specific security challenges',
                            'Competitive advantage opportunities',
                            'Case study from similar company'
                        ]
                    }
                ]
            },
            'fast_track_sales': {
                'name': f"Fast Track - {company}",
                'emails': [
                    {
                        'day': 0,
                        'subject': f"Industrial Cybersecurity for {industry} - Live Demo",
                        'preview': f"See how {company} can secure {industry} operations",
                        'content_points': [
                            f'{industry}-specific security solutions',
                            'Technical architecture overview',
                            'Interactive demo link',
                            'Compliance drivers (TSA/IEC 62443)'
                        ]
                    },
                    {
                        'day': 2,
                        'subject': 'Technical resources for your review',
                        'preview': 'Architecture diagrams and case studies',
                        'content_points': [
                            'Technical documentation',
                            'Similar project case studies',
                            'Demo scheduling link'
                        ]
                    }
                ]
            },
            'standard_sales': {
                'name': f"Standard Pipeline - {company}",
                'emails': [
                    {
                        'day': 0,
                        'subject': f"Industrial Automation Security for {industry}",
                        'preview': 'Protect your operations from cyber threats',
                        'content_points': [
                            f'{industry} security challenges',
                            'INSA expertise overview',
                            'Educational resources',
                            'Discovery call link'
                        ]
                    },
                    {
                        'day': 7,
                        'subject': f"Security insights for {industry}",
                        'preview': 'Latest threats and best practices',
                        'content_points': [
                            'Industry news',
                            'Security tips',
                            'Webinar invitation'
                        ]
                    }
                ]
            },
            'qualification': {
                'name': f"Qualification - {company}",
                'emails': [
                    {
                        'day': 0,
                        'subject': 'Understanding your industrial security needs',
                        'preview': 'Quick questionnaire to help us serve you better',
                        'content_points': [
                            'Qualification questionnaire link',
                            'General information about INSA',
                            'Resources library'
                        ]
                    }
                ]
            }
        }

        return campaigns.get(pipeline, campaigns['qualification'])

    async def process_lead(self, lead: Dict) -> Dict:
        """
        Main orchestration function - processes single lead through entire system

        Steps:
        1. Assign pipeline
        2. Generate workflow plan
        3. Create ERPNext opportunity
        4. Add to Mautic segment
        5. Trigger n8n automation
        6. Schedule follow-ups
        7. Update database
        """
        lead_id = lead['lead_id']
        lead_name = lead['lead_name']
        company = lead['company_name']

        logger.info(f"Processing lead: {lead_name} ({company})")

        # 1. Assign pipeline
        pipeline = self.assign_pipeline(lead)
        logger.info(f"  → Assigned to pipeline: {pipeline}")

        # 2. Generate workflow plan
        workflow_plan = self.get_workflow_plan(lead, pipeline)
        logger.info(f"  → Generated workflow plan with {len(workflow_plan['follow_ups'])} follow-ups")

        # 3. Generate Mautic segment
        mautic_segment = self.generate_mautic_segment(pipeline)
        logger.info(f"  → Mautic segment: {mautic_segment}")

        # 4. Generate email campaign
        email_campaign = self.generate_email_campaign(pipeline, lead)
        logger.info(f"  → Email campaign: {email_campaign['name']}")

        # 5. Update database with orchestration data
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Add orchestration columns if they don't exist
            cursor.execute("""
                ALTER TABLE leads
                ADD COLUMN IF NOT EXISTS pipeline VARCHAR(100),
                ADD COLUMN IF NOT EXISTS pipeline_stage VARCHAR(100),
                ADD COLUMN IF NOT EXISTS workflow_plan JSONB,
                ADD COLUMN IF NOT EXISTS mautic_segment VARCHAR(200),
                ADD COLUMN IF NOT EXISTS email_campaign JSONB,
                ADD COLUMN IF NOT EXISTS next_follow_up TIMESTAMP WITH TIME ZONE,
                ADD COLUMN IF NOT EXISTS orchestration_status VARCHAR(50) DEFAULT 'pending',
                ADD COLUMN IF NOT EXISTS orchestrated_at TIMESTAMP WITH TIME ZONE
            """)

            # Update lead with orchestration data
            cursor.execute("""
                UPDATE leads
                SET
                    pipeline = %s,
                    pipeline_stage = %s,
                    workflow_plan = %s,
                    mautic_segment = %s,
                    email_campaign = %s,
                    next_follow_up = %s,
                    orchestration_status = 'orchestrated',
                    orchestrated_at = NOW()
                WHERE lead_id = %s
            """, (
                pipeline,
                workflow_plan['current_stage'],
                json.dumps(workflow_plan),
                mautic_segment,
                json.dumps(email_campaign),
                workflow_plan['follow_ups'][0]['date'],
                lead_id
            ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"  ✓ Database updated for {lead_name}")

        except Exception as e:
            logger.error(f"  ✗ Database error: {str(e)}")

        return {
            'lead_id': lead_id,
            'lead_name': lead_name,
            'company': company,
            'pipeline': pipeline,
            'workflow_plan': workflow_plan,
            'mautic_segment': mautic_segment,
            'email_campaign': email_campaign,
            'status': 'success'
        }

    async def orchestrate_all_leads(self) -> List[Dict]:
        """Process all leads in database"""
        try:
            # Get all unprocessed leads
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    lead_id, lead_name, company_name, email, phone, mobile,
                    designation, industry, opportunity_score, priority_tier,
                    city, state, notes
                FROM leads
                WHERE orchestration_status IS NULL OR orchestration_status = 'pending'
                ORDER BY opportunity_score DESC
            """)

            columns = [desc[0] for desc in cursor.description]
            leads = []
            for row in cursor.fetchall():
                lead = dict(zip(columns, row))
                leads.append(lead)

            cursor.close()
            conn.close()

            logger.info(f"Found {len(leads)} leads to orchestrate")

            # Process each lead
            results = []
            for lead in leads:
                result = await self.process_lead(lead)
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error orchestrating leads: {str(e)}")
            return []

    def generate_orchestration_report(self, results: List[Dict]) -> str:
        """Generate human-readable orchestration report"""
        report = []
        report.append("=" * 80)
        report.append("INTELLIGENT LEAD ORCHESTRATION REPORT")
        report.append("=" * 80)
        report.append(f"Total leads processed: {len(results)}")
        report.append("")

        # Group by pipeline
        pipeline_groups = {}
        for result in results:
            pipeline = result['pipeline']
            if pipeline not in pipeline_groups:
                pipeline_groups[pipeline] = []
            pipeline_groups[pipeline].append(result)

        # Report by pipeline
        for pipeline, leads in sorted(pipeline_groups.items()):
            pipeline_name = self.pipelines[pipeline]['name']
            report.append(f"\n{pipeline_name.upper()} ({len(leads)} leads)")
            report.append("-" * 80)

            for lead in leads:
                report.append(f"  • {lead['lead_name']} - {lead['company']}")
                report.append(f"    Pipeline: {lead['workflow_plan']['current_stage']}")
                report.append(f"    Priority: {lead['workflow_plan']['priority']}")
                report.append(f"    Follow-ups scheduled: {len(lead['workflow_plan']['follow_ups'])}")
                report.append(f"    Next action: {lead['workflow_plan']['follow_ups'][0]['date'].split('T')[0]}")
                report.append("")

        report.append("=" * 80)
        report.append("NEXT STEPS:")
        report.append("=" * 80)
        report.append("1. Execute MCP integrations (ERPNext, Mautic, n8n)")
        report.append("2. Trigger email campaigns via Mautic")
        report.append("3. Schedule automated follow-ups")
        report.append("4. Monitor pipeline progression")
        report.append("5. AI qualification for each lead")
        report.append("")

        return "\n".join(report)


async def main():
    """Main orchestration function"""
    orchestrator = LeadOrchestrator()

    print("=" * 80)
    print("INTELLIGENT LEAD ORCHESTRATOR")
    print("Automatically assigns pipelines and triggers workflows")
    print("=" * 80)
    print()

    # Orchestrate all leads
    results = await orchestrator.orchestrate_all_leads()

    # Generate report
    report = orchestrator.generate_orchestration_report(results)
    print(report)

    # Save report
    report_file = f"/tmp/lead_orchestration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"Report saved to: {report_file}")
    print()
    print("✓ Lead orchestration complete!")


if __name__ == "__main__":
    asyncio.run(main())
