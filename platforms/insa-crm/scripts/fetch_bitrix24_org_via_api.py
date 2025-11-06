#!/usr/bin/env python3
"""
Fetch INSA Organizational Structure from Bitrix24 via REST API
Uses the existing INSA CRM API that has Bitrix24 data
"""

import requests
import json
from datetime import datetime

# INSA CRM API (already has Bitrix24 data synced)
INSA_API_BASE = "http://100.100.101.1:8003/api/v1/bitrix24"
AUTH = ("admin", "admin")

class INSAOrganizationAnalyzer:
    """Analyze INSA organizational structure from Bitrix24 data"""

    def __init__(self):
        self.session = requests.Session()
        self.session.auth = AUTH

    def get_email_users(self):
        """Get users from email response metrics"""
        try:
            response = self.session.get(f"{INSA_API_BASE}/emails/response-metrics")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_quote_users(self):
        """Get users from quote conversion metrics"""
        try:
            response = self.session.get(f"{INSA_API_BASE}/quotes/conversion-metrics")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def analyze_organization(self):
        """Build organizational structure from available data"""
        print("="*70)
        print("🏭 INSA INGENIERÍA - Organizational Analysis")
        print("="*70)

        # Get data from API
        email_users = self.get_email_users()
        quote_users = self.get_quote_users()

        # Extract unique users
        all_users = {}

        print(f"\n📊 Found {len(email_users)} users in email metrics")
        for user in email_users:
            name = user.get('user_name', 'Unknown')
            all_users[name] = {
                'name': name,
                'email_count': user.get('total_emails', 0),
                'sla_compliance': user.get('sla_compliance_percentage', 0),
                'avg_response_time': user.get('avg_response_time_hours', 0),
                'role': self.infer_role_from_name(name),
                'department': self.infer_department_from_role(self.infer_role_from_name(name))
            }

        print(f"📊 Found {len(quote_users)} users in quote metrics")
        for user in quote_users:
            name = user.get('user_name', 'Unknown')
            if name in all_users:
                all_users[name]['quotes_sent'] = user.get('quotes_sent', 0)
                all_users[name]['quotes_won'] = user.get('quotes_won', 0)
                all_users[name]['conversion_rate'] = user.get('conversion_rate', 0)
            else:
                all_users[name] = {
                    'name': name,
                    'quotes_sent': user.get('quotes_sent', 0),
                    'quotes_won': user.get('quotes_won', 0),
                    'conversion_rate': user.get('conversion_rate', 0),
                    'role': self.infer_role_from_activity(user),
                    'department': self.infer_department_from_role(self.infer_role_from_activity(user))
                }

        # Create org structure
        org_structure = {
            'company_name': 'INSA Ingeniería',
            'analysis_date': datetime.now().isoformat(),
            'total_employees': len(all_users),
            'employees': list(all_users.values()),
            'departments': self.build_departments(all_users),
            'roles': self.get_unique_roles(all_users)
        }

        return org_structure

    def infer_role_from_name(self, name):
        """Infer role from name patterns"""
        name_lower = name.lower()

        # Known patterns
        if 'aroca' in name_lower or 'wil' in name_lower:
            return 'CEO / Founder'
        elif 'casas' in name_lower or 'juan' in name_lower:
            return 'Sales Manager'
        elif 'ingeniero' in name_lower or 'engineer' in name_lower:
            return 'Lead Mechanical Engineer'
        elif 'gerente' in name_lower or 'manager' in name_lower:
            return 'Sales Manager'
        elif 'vendedor' in name_lower or 'sales' in name_lower:
            return 'Sales Representative'
        else:
            return 'Employee'

    def infer_role_from_activity(self, user_data):
        """Infer role from activity metrics"""
        quotes_sent = user_data.get('quotes_sent', 0)
        conversion_rate = user_data.get('conversion_rate', 0)

        if quotes_sent > 20:
            if conversion_rate > 30:
                return 'Senior Sales Representative'
            else:
                return 'Sales Representative'
        elif quotes_sent > 0:
            return 'Sales Engineer'
        else:
            return 'Employee'

    def infer_department_from_role(self, role):
        """Map role to department"""
        role_lower = role.lower()

        if 'ceo' in role_lower or 'founder' in role_lower:
            return 'Executive'
        elif 'sales' in role_lower or 'vendedor' in role_lower:
            return 'Sales'
        elif 'engineer' in role_lower or 'ingeniero' in role_lower:
            return 'Engineering'
        elif 'project' in role_lower:
            return 'Project Management'
        elif 'admin' in role_lower:
            return 'Administration'
        else:
            return 'General'

    def build_departments(self, users):
        """Build department structure"""
        departments = {}

        for user in users.values():
            dept = user.get('department', 'General')
            if dept not in departments:
                departments[dept] = {
                    'name': dept,
                    'employees': [],
                    'head': None
                }
            departments[dept]['employees'].append(user['name'])

            # Set department head for CEO
            if user['role'] == 'CEO / Founder':
                departments[dept]['head'] = user['name']

        return list(departments.values())

    def get_unique_roles(self, users):
        """Get list of unique roles"""
        roles = set()
        for user in users.values():
            roles.add(user.get('role', 'Employee'))
        return sorted(list(roles))

    def print_summary(self, org_structure):
        """Print organizational summary"""
        print(f"\n🏢 Company: {org_structure['company_name']}")
        print(f"👥 Total Employees: {org_structure['total_employees']}")
        print(f"🏭 Departments: {len(org_structure['departments'])}")

        print("\n📊 DEPARTMENTS:")
        for dept in org_structure['departments']:
            print(f"  - {dept['name']}: {len(dept['employees'])} employees")
            if dept['head']:
                print(f"    Head: {dept['head']}")

        print("\n💼 ROLES IDENTIFIED:")
        for i, role in enumerate(org_structure['roles'], 1):
            employees_with_role = [e for e in org_structure['employees'] if e['role'] == role]
            print(f"  {i}. {role} ({len(employees_with_role)} employees)")

        print("\n👤 EMPLOYEES:")
        for employee in org_structure['employees']:
            print(f"\n  {employee['name']}")
            print(f"    Role: {employee['role']}")
            print(f"    Department: {employee['department']}")
            if 'email_count' in employee:
                print(f"    Emails: {employee['email_count']}, SLA: {employee['sla_compliance']:.1f}%")
            if 'quotes_sent' in employee:
                print(f"    Quotes: {employee['quotes_sent']}, Win Rate: {employee.get('conversion_rate', 0):.1f}%")

    def save_to_file(self, org_structure):
        """Save to JSON file"""
        filename = "insa_organization_structure.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(org_structure, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved to: {filename}")
        return filename

def main():
    print("\n🚀 Fetching INSA Organization Structure...")

    analyzer = INSAOrganizationAnalyzer()
    org_structure = analyzer.analyze_organization()
    analyzer.print_summary(org_structure)
    analyzer.save_to_file(org_structure)

    print("\n✅ Analysis complete!")
    print("\n💡 Next: Use this data to build role-based CRM V7")

if __name__ == "__main__":
    main()
