import os
import re
from pathlib import Path
import pandas as pd
import PyPDF2
from collections import defaultdict
import json
from datetime import datetime

class GRSDocumentAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.documents = []
        self.analysis_results = {
            'total_documents': 0,
            'categories': defaultdict(int),
            'grs_numbers': [],
            'document_types': defaultdict(int),
            'retention_periods': defaultdict(int),
            'document_sizes': [],
            'metadata': []
        }

    def extract_grs_number(self, filename):
        match = re.search(r'GRS-(\d+)', filename)
        return match.group(1) if match else None

    def extract_document_type(self, filename):
        # Extract the main document type from the filename
        # Example: "zoning-maps-(GRS-23356).pdf" -> "zoning maps"
        doc_type = filename.split('-(GRS')[0].replace('-', ' ').strip()
        return doc_type

    def extract_text_from_pdf(self, pdf_path):
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() + '\n'
                return text
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            return ''

    def extract_retention_period(self, text):
        # Look for retention period information in the text
        retention_patterns = [
            r'RETENTION:\s*(.*?)\n',
            r'Retain for\s*(.*?)\n',
            r'retained for\s*(.*?)\n'
        ]
        
        for pattern in retention_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Not specified"

    def analyze_documents(self):
        pdf_files = list(self.data_dir.glob('*.pdf'))
        self.analysis_results['total_documents'] = len(pdf_files)

        for pdf_path in pdf_files:
            filename = pdf_path.name
            text = self.extract_text_from_pdf(pdf_path)
            
            # Extract document metadata
            grs_number = self.extract_grs_number(filename)
            doc_type = self.extract_document_type(filename)
            retention_period = self.extract_retention_period(text)
            file_size = os.path.getsize(pdf_path)

            # Update analysis results
            self.analysis_results['grs_numbers'].append(grs_number)
            self.analysis_results['document_types'][doc_type] += 1
            self.analysis_results['retention_periods'][retention_period] += 1
            self.analysis_results['document_sizes'].append(file_size)

            # Categorize documents
            main_category = doc_type.split()[0]  # Use first word as main category
            self.analysis_results['categories'][main_category] += 1

            # Store detailed metadata
            metadata = {
                'filename': filename,
                'grs_number': grs_number,
                'document_type': doc_type,
                'retention_period': retention_period,
                'file_size': file_size,
                'main_category': main_category
            }
            self.analysis_results['metadata'].append(metadata)

    def generate_report(self):
        # Convert analysis results to DataFrame for easier manipulation
        df = pd.DataFrame(self.analysis_results['metadata'])
        
        report = {
            'summary': {
                'total_documents': self.analysis_results['total_documents'],
                'unique_categories': len(self.analysis_results['categories']),
                'total_size_mb': sum(self.analysis_results['document_sizes']) / (1024 * 1024)
            },
            'categories': dict(self.analysis_results['categories']),
            'document_types': dict(self.analysis_results['document_types']),
            'retention_periods': dict(self.analysis_results['retention_periods']),
            'statistics': {
                'avg_file_size_kb': df['file_size'].mean() / 1024,
                'min_file_size_kb': df['file_size'].min() / 1024,
                'max_file_size_kb': df['file_size'].max() / 1024
            }
        }

        # Save detailed report to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.data_dir / f'grs_analysis_report_{timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Save detailed metadata to CSV
        csv_path = self.data_dir / f'grs_documents_metadata_{timestamp}.csv'
        df.to_csv(csv_path, index=False)

        return report, report_path, csv_path

def main():
    # Initialize analyzer with data directory
    analyzer = GRSDocumentAnalyzer('data')
    
    print("Starting GRS document analysis...")
    analyzer.analyze_documents()
    
    print("\nGenerating analysis report...")
    report, report_path, csv_path = analyzer.generate_report()
    
    print("\nAnalysis Summary:")
    print(f"Total Documents: {report['summary']['total_documents']}")
    print(f"Unique Categories: {report['summary']['unique_categories']}")
    print(f"Total Size: {report['summary']['total_size_mb']:.2f} MB")
    
    print("\nTop Categories:")
    for category, count in sorted(report['categories'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{category}: {count} documents")
    
    print(f"\nDetailed report saved to: {report_path}")
    print(f"Metadata CSV saved to: {csv_path}")

if __name__ == "__main__":
    main() 