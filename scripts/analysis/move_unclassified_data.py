import os
import shutil
from pathlib import Path
import json
from datetime import datetime

class UnclassifiedDataMover:
    def __init__(self, source_dir, classified_dir, unclassified_dir):
        self.source_dir = Path(source_dir)
        self.classified_dir = Path(classified_dir)
        self.unclassified_dir = Path(unclassified_dir)
        self.stats = {
            'total_files': 0,
            'classified_files': 0,
            'unclassified_files': 0,
            'unclassified_types': {}
        }

    def get_classified_files(self):
        """Get a set of all files in the classified directory structure"""
        classified_files = set()
        for root, _, files in os.walk(self.classified_dir):
            for file in files:
                if file.endswith('.pdf'):
                    classified_files.add(file)
        return classified_files

    def identify_unclassified(self):
        """Identify files that are not in any classification"""
        classified_files = self.get_classified_files()
        unclassified_files = []
        
        for file in self.source_dir.glob('*.pdf'):
            self.stats['total_files'] += 1
            if file.name not in classified_files:
                unclassified_files.append(file)
                doc_type = file.name.split('-(GRS')[0].replace('-', ' ').strip()
                self.stats['unclassified_types'][doc_type] = self.stats['unclassified_types'].get(doc_type, 0) + 1
                self.stats['unclassified_files'] += 1
            else:
                self.stats['classified_files'] += 1
                
        return unclassified_files

    def move_unclassified(self):
        """Move unclassified files to the unclassified directory"""
        print("Starting to move unclassified files...")
        
        # Create unclassified directory if it doesn't exist
        self.unclassified_dir.mkdir(parents=True, exist_ok=True)
        
        # Get unclassified files
        unclassified_files = self.identify_unclassified()
        
        # Move files
        for file in unclassified_files:
            target_path = self.unclassified_dir / file.name
            shutil.copy2(file, target_path)
            print(f"Moved: {file.name}")

    def generate_report(self):
        """Generate a report of the unclassified data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report = {
            'summary': {
                'total_files': self.stats['total_files'],
                'classified_files': self.stats['classified_files'],
                'unclassified_files': self.stats['unclassified_files'],
                'unclassified_percentage': (self.stats['unclassified_files'] / self.stats['total_files'] * 100) if self.stats['total_files'] > 0 else 0
            },
            'unclassified_types': dict(sorted(
                self.stats['unclassified_types'].items(),
                key=lambda x: x[1],
                reverse=True
            ))
        }
        
        # Save report
        report_path = self.unclassified_dir / f'unclassified_report_{timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report, report_path

def main():
    # Set up directories
    source_dir = 'data'
    classified_dir = 'data/classified_grs'
    unclassified_dir = 'data/unclassified_grs'
    
    # Initialize and run mover
    mover = UnclassifiedDataMover(source_dir, classified_dir, unclassified_dir)
    
    print(f"Analyzing files in {source_dir}...")
    mover.move_unclassified()
    
    print("\nGenerating report...")
    report, report_path = mover.generate_report()
    
    # Print summary
    print("\nUnclassified Data Summary:")
    print(f"Total Files: {report['summary']['total_files']}")
    print(f"Classified Files: {report['summary']['classified_files']}")
    print(f"Unclassified Files: {report['summary']['unclassified_files']}")
    print(f"Unclassified Percentage: {report['summary']['unclassified_percentage']:.1f}%")
    
    print("\nTop 10 Unclassified Document Types:")
    for doc_type, count in list(report['unclassified_types'].items())[:10]:
        print(f"{doc_type}: {count} files")
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main() 