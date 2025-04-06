import os
from pathlib import Path
import json
from collections import defaultdict
import re
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans

class OtherCategoryAnalyzer:
    def __init__(self, other_dir):
        self.other_dir = Path(other_dir)
        self.stats = {
            'total_documents': 0,
            'word_frequencies': defaultdict(int),
            'common_patterns': defaultdict(list),
            'suggested_categories': defaultdict(list)
        }
        
        # Common words that might indicate categories
        self.category_indicators = {
            'financial': ['budget', 'payment', 'financial', 'accounting', 'tax', 'revenue', 'expense'],
            'administrative': ['policy', 'procedure', 'administrative', 'management', 'organization'],
            'legal': ['legal', 'court', 'case', 'law', 'regulation', 'compliance'],
            'personnel': ['employee', 'staff', 'personnel', 'hr', 'employment', 'training'],
            'records': ['record', 'document', 'file', 'archive', 'documentation'],
            'property': ['property', 'building', 'facility', 'construction', 'maintenance'],
            'public_services': ['service', 'public', 'community', 'utility', 'program']
        }

    def extract_document_type(self, filename):
        """Extract document type from filename"""
        return filename.split('-(GRS')[0].replace('-', ' ').strip()

    def analyze_documents(self):
        """Analyze documents in the other category"""
        print("Analyzing documents in 'other' category...")
        
        # Collect document types and text
        document_types = []
        for file in self.other_dir.glob('*.pdf'):
            self.stats['total_documents'] += 1
            doc_type = self.extract_document_type(file.name)
            document_types.append(doc_type)
            
            # Update word frequencies
            words = doc_type.lower().split()
            for word in words:
                self.stats['word_frequencies'][word] += 1

        # Perform clustering on document types
        if document_types:
            vectorizer = CountVectorizer(stop_words='english')
            X = vectorizer.fit_transform(document_types)
            
            # Determine optimal number of clusters (max 20)
            n_clusters = min(20, len(document_types))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans.fit(X)
            
            # Analyze clusters
            feature_names = vectorizer.get_feature_names_out()
            for i in range(n_clusters):
                cluster_center = kmeans.cluster_centers_[i]
                top_features_idx = cluster_center.argsort()[-5:][::-1]  # Top 5 features
                top_terms = [feature_names[idx] for idx in top_features_idx]
                
                # Get documents in this cluster
                cluster_docs = [doc for doc, label in zip(document_types, kmeans.labels_) if label == i]
                
                self.stats['common_patterns'][f"Cluster_{i}"] = {
                    'top_terms': top_terms,
                    'document_count': len(cluster_docs),
                    'example_documents': cluster_docs[:5]
                }

        # Suggest new categories based on word frequencies
        for word, freq in sorted(self.stats['word_frequencies'].items(), key=lambda x: x[1], reverse=True):
            for category, indicators in self.category_indicators.items():
                if word in indicators:
                    self.stats['suggested_categories'][category].append((word, freq))

    def generate_report(self):
        """Generate analysis report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report = {
            'summary': {
                'total_documents': self.stats['total_documents'],
                'unique_words': len(self.stats['word_frequencies'])
            },
            'word_frequencies': dict(sorted(
                self.stats['word_frequencies'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:100]),  # Top 100 words
            'common_patterns': self.stats['common_patterns'],
            'suggested_categories': {
                category: sorted(words, key=lambda x: x[1], reverse=True)
                for category, words in self.stats['suggested_categories'].items()
            }
        }
        
        # Save report
        report_path = self.other_dir / f'other_category_analysis_{timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report, report_path

    def print_summary(self, report):
        """Print analysis summary"""
        print("\nOther Category Analysis Summary:")
        print(f"Total Documents: {report['summary']['total_documents']}")
        print(f"Unique Words: {report['summary']['unique_words']}")
        
        print("\nTop 20 Most Common Words:")
        for word, freq in list(report['word_frequencies'].items())[:20]:
            print(f"{word}: {freq}")
        
        print("\nSuggested New Categories:")
        for category, words in report['suggested_categories'].items():
            if words:
                print(f"\n{category.title()}:")
                for word, freq in words[:5]:  # Show top 5 words per category
                    print(f"  - {word} ({freq} occurrences)")
        
        print("\nLargest Document Clusters:")
        sorted_clusters = sorted(
            report['common_patterns'].items(),
            key=lambda x: x[1]['document_count'],
            reverse=True
        )
        for cluster_name, cluster_info in sorted_clusters[:5]:
            print(f"\n{cluster_name}:")
            print(f"  Documents: {cluster_info['document_count']}")
            print(f"  Top terms: {', '.join(cluster_info['top_terms'])}")
            print(f"  Examples: {', '.join(cluster_info['example_documents'][:3])}")

def main():
    other_dir = 'data/classified_grs/other'
    
    # Initialize and run analyzer
    analyzer = OtherCategoryAnalyzer(other_dir)
    
    print(f"Analyzing documents in {other_dir}...")
    analyzer.analyze_documents()
    
    print("\nGenerating report...")
    report, report_path = analyzer.generate_report()
    
    # Print summary
    analyzer.print_summary(report)
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main() 