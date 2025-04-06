import os
import shutil
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict

class DocumentReorganizer:
    def __init__(self, other_dir):
        self.other_dir = Path(other_dir)
        self.new_categories = {
            'reports_and_documentation': {
                'keywords': ['report', 'documentation', 'annual', 'monthly', 'summary'],
                'subcategories': {
                    'annual_reports': ['annual report'],
                    'monthly_reports': ['monthly report', 'monthly summary'],
                    'program_reports': ['program report', 'project report'],
                    'technical_documentation': ['technical', 'documentation', 'manual'],
                    'audit_reports': ['audit report']
                }
            },
            'case_management': {
                'keywords': ['case', 'cases', 'family', 'child', 'welfare'],
                'subcategories': {
                    'family_cases': ['family case', 'domestic'],
                    'child_services': ['child', 'juvenile', 'youth'],
                    'welfare_cases': ['welfare', 'assistance', 'support'],
                    'program_cases': ['program case'],
                    'grant_cases': ['grant case']
                }
            },
            'program_administration': {
                'keywords': ['program', 'conference', 'grant', 'nutrition'],
                'subcategories': {
                    'program_files': ['program files'],
                    'conference_files': ['conference', 'meeting files'],
                    'grant_programs': ['grant program'],
                    'nutrition_programs': ['nutrition', 'food service'],
                    'community_programs': ['community program']
                }
            },
            'regulatory_compliance': {
                'keywords': ['registration', 'license', 'compliance', 'regulation'],
                'subcategories': {
                    'registration_records': ['registration'],
                    'licensing_files': ['license', 'licensing'],
                    'compliance_reports': ['compliance'],
                    'regulatory_docs': ['regulation', 'regulatory']
                }
            },
            'meeting_records': {
                'keywords': ['minutes', 'meeting', 'board', 'committee'],
                'subcategories': {
                    'board_minutes': ['board minutes'],
                    'committee_minutes': ['committee minutes'],
                    'conference_records': ['conference records'],
                    'meeting_docs': ['meeting documentation']
                }
            }
        }
        self.stats = defaultdict(lambda: defaultdict(int))

    def determine_category(self, doc_type):
        """Determine the appropriate category and subcategory for a document"""
        doc_type_lower = doc_type.lower()
        
        # Check each category
        for category, info in self.new_categories.items():
            if any(keyword in doc_type_lower for keyword in info['keywords']):
                # Check subcategories
                for subcategory, keywords in info['subcategories'].items():
                    if any(keyword in doc_type_lower for keyword in keywords):
                        return category, subcategory
                return category, 'general'  # Default subcategory
        
        return 'uncategorized', 'general'

    def create_directory_structure(self):
        """Create the new directory structure"""
        for category in self.new_categories.keys():
            category_dir = self.other_dir.parent / category
            category_dir.mkdir(exist_ok=True)
            
            # Create subcategory directories
            for subcategory in self.new_categories[category]['subcategories'].keys():
                subcategory_dir = category_dir / subcategory
                subcategory_dir.mkdir(exist_ok=True)
            
            # Create general subcategory
            (category_dir / 'general').mkdir(exist_ok=True)

    def reorganize_documents(self):
        """Reorganize documents into new categories"""
        print("Starting document reorganization...")
        
        # Create new directory structure
        self.create_directory_structure()
        
        # Process each document
        total_files = len(list(self.other_dir.glob('*.pdf')))
        processed = 0
        
        for file in self.other_dir.glob('*.pdf'):
            processed += 1
            if processed % 100 == 0:
                print(f"Processing: {processed}/{total_files} documents...")
            
            doc_type = file.name.split('-(GRS')[0].replace('-', ' ').strip()
            category, subcategory = self.determine_category(doc_type)
            
            # Create target directory and move file
            if category != 'uncategorized':
                target_dir = self.other_dir.parent / category / subcategory
            else:
                target_dir = self.other_dir.parent / 'other' / 'general'
            
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / file.name
            
            # Move the file instead of copying
            try:
                shutil.move(str(file), str(target_path))
                # Update stats
                self.stats[category][subcategory] += 1
            except (shutil.Error, OSError) as e:
                print(f"Error moving {file.name}: {str(e)}")

    def generate_report(self):
        """Generate a report of the reorganization"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report = {
            'summary': {
                'total_documents': sum(
                    sum(subcats.values())
                    for cats in self.stats.values()
                    for subcats in [cats]
                ),
                'categories': {
                    category: {
                        'total': sum(subcats.values()),
                        'subcategories': dict(subcats)
                    }
                    for category, subcats in self.stats.items()
                }
            }
        }
        
        # Save report
        report_path = self.other_dir.parent / f'reorganization_report_{timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report, report_path

    def print_summary(self, report):
        """Print reorganization summary"""
        print("\nDocument Reorganization Summary:")
        print(f"Total Documents Processed: {report['summary']['total_documents']}")
        
        print("\nCategory Distribution:")
        for category, info in report['summary']['categories'].items():
            if info['total'] > 0:
                print(f"\n{category.replace('_', ' ').title()} ({info['total']} documents):")
                for subcategory, count in info['subcategories'].items():
                    if count > 0:
                        print(f"  - {subcategory.replace('_', ' ').title()}: {count}")

def main():
    other_dir = 'data/classified_grs/other'
    
    # Initialize and run reorganizer
    reorganizer = DocumentReorganizer(other_dir)
    
    print(f"Reorganizing documents from {other_dir}...")
    reorganizer.reorganize_documents()
    
    print("\nGenerating report...")
    report, report_path = reorganizer.generate_report()
    
    # Print summary
    reorganizer.print_summary(report)
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main() 