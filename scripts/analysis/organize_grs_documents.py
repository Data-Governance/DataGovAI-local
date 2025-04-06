import os
import re
import shutil
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class GRSDocumentOrganizer:
    def __init__(self, source_dir, target_base_dir):
        self.source_dir = Path(source_dir)
        self.target_base_dir = Path(target_base_dir)
        self.classification_map = {
            # Administrative & Governance
            'administrative': ['administrative', 'policy', 'policies', 'ordinance', 'resolution', 'council'],
            'financial': ['budget', 'payroll', 'account', 'audit', 'financial', 'tax'],
            'public_services': ['water', 'public', 'city', 'building', 'cemetery', 'utility'],
            'legal': ['civil', 'criminal', 'warrant', 'court', 'legal', 'enforcement'],
            'education': ['student', 'school', 'training', 'educational'],
            'personnel': ['personnel', 'employee', 'staff', 'employment'],
            'health': ['medical', 'health', 'patient', 'pharmacy'],
            'property': ['property', 'land', 'building', 'zoning', 'planning'],
            'records_management': ['record', 'document', 'file', 'archive'],
        }
        self.stats = defaultdict(int)
        self.document_metadata = []

    def create_directory_structure(self):
        """Create the classified directory structure"""
        for category in self.classification_map.keys():
            category_path = self.target_base_dir / category
            category_path.mkdir(parents=True, exist_ok=True)

    def determine_category(self, document_type):
        """Determine the appropriate category for a document"""
        document_words = set(document_type.lower().split())
        
        for category, keywords in self.classification_map.items():
            if any(keyword in document_words for keyword in keywords):
                return category
        return 'other'

    def extract_metadata(self, filepath):
        """Extract metadata from filename"""
        filename = filepath.name
        doc_type = filename.split('-(GRS')[0].replace('-', ' ').strip()
        grs_match = re.search(r'GRS-(\d+)', filename)
        grs_number = grs_match.group(1) if grs_match else None
        return {
            'filename': filename,
            'document_type': doc_type,
            'grs_number': grs_number,
            'original_path': str(filepath),
            'file_size': os.path.getsize(filepath)
        }

    def organize_documents(self):
        """Organize documents into classified directories"""
        print("Starting document organization...")
        
        # Create directory structure
        self.create_directory_structure()
        # Create 'other' category directory
        (self.target_base_dir / 'other').mkdir(parents=True, exist_ok=True)
        
        # Process each document
        total_files = len(list(self.source_dir.glob('*.pdf')))
        processed = 0
        
        for filepath in self.source_dir.glob('*.pdf'):
            processed += 1
            if processed % 100 == 0:
                print(f"Processing: {processed}/{total_files} documents...")
                
            metadata = self.extract_metadata(filepath)
            category = self.determine_category(metadata['document_type'])
            
            # Create target directory and copy file
            target_dir = self.target_base_dir / category
            target_dir.mkdir(parents=True, exist_ok=True)  # Ensure category directory exists
            target_path = target_dir / filepath.name
            
            # Copy the file
            shutil.copy2(filepath, target_path)
            
            # Update metadata and stats
            metadata['category'] = category
            metadata['new_path'] = str(target_path)
            self.document_metadata.append(metadata)
            self.stats[category] += 1
        
        print(f"Completed processing {total_files} documents.")

    def generate_report(self):
        """Generate a comprehensive report of the organization"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Convert metadata to DataFrame for analysis
        df = pd.DataFrame(self.document_metadata)
        
        report = {
            'summary': {
                'total_documents': len(self.document_metadata),
                'categories': dict(self.stats),
                'total_size_mb': sum(m['file_size'] for m in self.document_metadata) / (1024 * 1024)
            },
            'category_statistics': {
                category: {
                    'document_count': self.stats[category],
                    'percentage': (self.stats[category] / len(self.document_metadata)) * 100
                }
                for category in self.classification_map.keys()
            },
            'document_types': df['document_type'].value_counts().to_dict()
        }
        
        # Save detailed report
        report_path = self.target_base_dir / f'organization_report_{timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save detailed metadata CSV
        csv_path = self.target_base_dir / f'document_metadata_{timestamp}.csv'
        df.to_csv(csv_path, index=False)
        
        return report, report_path, csv_path

    def print_summary(self, report):
        """Print a summary of the organization"""
        print("\nDocument Organization Summary:")
        print(f"Total Documents Processed: {report['summary']['total_documents']}")
        print(f"Total Size: {report['summary']['total_size_mb']:.2f} MB")
        
        print("\nCategory Distribution:")
        for category, stats in report['category_statistics'].items():
            if stats['document_count'] > 0:
                print(f"{category}: {stats['document_count']} documents ({stats['percentage']:.1f}%)")

def main():
    # Set up source and target directories
    source_dir = 'data'
    target_dir = 'data/classified_grs'
    
    # Initialize and run organizer
    organizer = GRSDocumentOrganizer(source_dir, target_dir)
    
    print(f"Organizing documents from {source_dir} into {target_dir}...")
    organizer.organize_documents()
    
    print("\nGenerating comprehensive report...")
    report, report_path, csv_path = organizer.generate_report()
    
    # Print summary
    organizer.print_summary(report)
    
    print(f"\nDetailed report saved to: {report_path}")
    print(f"Metadata CSV saved to: {csv_path}")

if __name__ == "__main__":
    main() 