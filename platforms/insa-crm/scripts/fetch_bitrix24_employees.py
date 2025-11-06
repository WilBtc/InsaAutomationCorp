#!/usr/bin/env python3
"""
Fetch Real Employee & Organizational Data from Bitrix24
Uses Bitrix24 webhook to get actual INSA organizational structure
"""

import requests
import json
from datetime import datetime

# Bitrix24 webhook (replace with actual webhook URL)
# Format: https://insaingenieria.bitrix24.com/rest/1/webhook_code/
BITRIX24_WEBHOOK = "https://insaingenieria.bitrix24.com/rest/1/xmw6n5ygcaoz8wnf/"  # Replace with actual

class Bitrix24OrganizationFetcher:
    """Fetch organizational structure from Bitrix24"""

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url.rstrip('/')

    def call_api(self, method, params={}):
        """Call Bitrix24 REST API"""
        url = f"{self.webhook_url}/{method}"
        try:
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling {method}: {e}")
            return None

    def get_all_users(self):
        """Get all users/employees from Bitrix24"""
        print("📊 Fetching all users/employees...")
        result = self.call_api("user.get", {
            "ACTIVE": True  # Only active employees
        })

        if result and "result" in result:
            users = result["result"]
            print(f"✅ Found {len(users)} active employees")
            return users
        return []

    def get_departments(self):
        """Get all departments from Bitrix24"""
        print("\n🏢 Fetching departments...")
        result = self.call_api("department.get", {})

        if result and "result" in result:
            departments = result["result"]
            print(f"✅ Found {len(departments)} departments")
            return departments
        return []

    def get_user_fields(self):
        """Get custom user fields (for positions/titles)"""
        print("\n🔍 Fetching user field definitions...")
        result = self.call_api("user.fields", {})

        if result and "result" in result:
            fields = result["result"]
            print(f"✅ Found {len(fields)} user fields")
            return fields
        return {}

    def analyze_organization(self):
        """Analyze complete organizational structure"""
        print("\n" + "="*60)
        print("🏭 INSA Ingeniería - Organizational Structure Analysis")
        print("="*60)

        # Fetch data
        users = self.get_all_users()
        departments = self.get_departments()
        user_fields = self.get_user_fields()

        # Build organizational chart
        org_chart = {
            "company_name": "INSA Ingeniería",
            "total_employees": len(users),
            "total_departments": len(departments),
            "fetched_at": datetime.now().isoformat(),
            "departments": {},
            "employees": [],
            "positions": set(),
            "roles": set()
        }

        # Process departments
        dept_map = {}
        for dept in departments:
            dept_id = dept.get("ID")
            dept_name = dept.get("NAME", "Unknown")
            dept_map[dept_id] = {
                "id": dept_id,
                "name": dept_name,
                "parent_id": dept.get("PARENT"),
                "head_user_id": dept.get("UF_HEAD"),
                "employees": []
            }

        # Process employees
        for user in users:
            employee = {
                "id": user.get("ID"),
                "name": user.get("NAME"),
                "last_name": user.get("LAST_NAME"),
                "full_name": f"{user.get('NAME', '')} {user.get('LAST_NAME', '')}".strip(),
                "email": user.get("EMAIL"),
                "work_position": user.get("WORK_POSITION", ""),
                "personal_mobile": user.get("PERSONAL_MOBILE"),
                "personal_phone": user.get("PERSONAL_PHONE"),
                "work_phone": user.get("WORK_PHONE"),
                "department_ids": user.get("UF_DEPARTMENT", []),
                "is_admin": user.get("IS_ADMIN", False)
            }

            # Track positions and roles
            if employee["work_position"]:
                org_chart["positions"].add(employee["work_position"])

            # Add employee to departments
            for dept_id in employee["department_ids"]:
                if dept_id in dept_map:
                    dept_map[dept_id]["employees"].append(employee)

            org_chart["employees"].append(employee)

        # Convert to list
        org_chart["departments"] = list(dept_map.values())
        org_chart["positions"] = sorted(list(org_chart["positions"]))

        return org_chart

    def print_organization_summary(self, org_chart):
        """Print human-readable summary"""
        print("\n" + "="*60)
        print("📋 ORGANIZATIONAL SUMMARY")
        print("="*60)

        print(f"\n🏢 Company: {org_chart['company_name']}")
        print(f"👥 Total Employees: {org_chart['total_employees']}")
        print(f"🏭 Total Departments: {org_chart['total_departments']}")

        print("\n📊 DEPARTMENTS:")
        for dept in org_chart["departments"]:
            print(f"  - {dept['name']}: {len(dept['employees'])} employees")

        print("\n💼 POSITIONS FOUND:")
        for i, position in enumerate(org_chart["positions"], 1):
            employees_with_position = [e for e in org_chart["employees"] if e["work_position"] == position]
            print(f"  {i}. {position} ({len(employees_with_position)} employees)")

        print("\n👤 EMPLOYEE SAMPLE (first 10):")
        for employee in org_chart["employees"][:10]:
            print(f"  - {employee['full_name']}")
            print(f"    Position: {employee['work_position']}")
            print(f"    Email: {employee['email']}")
            print(f"    Departments: {employee['department_ids']}")
            print()

    def save_to_file(self, org_chart, filename="insa_organization_structure.json"):
        """Save organizational data to JSON file"""
        # Convert sets to lists for JSON serialization
        org_chart_copy = org_chart.copy()
        org_chart_copy["positions"] = list(org_chart_copy["positions"])
        org_chart_copy["roles"] = list(org_chart_copy["roles"])

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(org_chart_copy, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved organizational data to: {filename}")
        return filename

def main():
    """Main execution"""
    print("\n🚀 Starting Bitrix24 Organization Fetch...")
    print("="*60)

    # Initialize fetcher
    fetcher = Bitrix24OrganizationFetcher(BITRIX24_WEBHOOK)

    # Analyze organization
    org_chart = fetcher.analyze_organization()

    # Print summary
    fetcher.print_organization_summary(org_chart)

    # Save to file
    filename = fetcher.save_to_file(org_chart)

    print("\n✅ Organization fetch complete!")
    print(f"📁 Data saved to: {filename}")
    print("\n💡 Next steps:")
    print("  1. Review the JSON file for organizational structure")
    print("  2. Use this data to build role-based CRM V7")
    print("  3. Map positions to CRM workflows")

if __name__ == "__main__":
    main()
