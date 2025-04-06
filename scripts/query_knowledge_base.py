#!/usr/bin/env python
"""
Query Knowledge Base - Script to query the knowledge base using RAG+KG Query Agent.
"""
import os
import logging
import argparse
import json
from pprint import pprint

from src.knowledge_base_agent.config import get_config
from src.knowledge_base_agent.cli import create_processor, setup_logging
from src.knowledge_base_agent.query_agent import RAGKGQueryAgent

# Configure logging
logger = logging.getLogger(__name__)

def query_knowledge_base(query: str, config, use_advanced: bool = True, verbose: bool = False, 
                         limit: int = 5, min_score: float = 0.6) -> None:
    """Query the knowledge base using the processor.
    
    Args:
        query: Query string
        config: Configuration object
        use_advanced: Whether to use the advanced RAG+KG query agent
        verbose: Whether to display verbose results
        limit: Maximum number of results to return
        min_score: Minimum similarity score for vector results
    """
    # Create processor
    processor = create_processor(config)
    
    # Execute query
    if use_advanced:
        logger.info(f"Executing advanced RAG+KG query: {query}")
        
        # Create query agent
        query_agent = RAGKGQueryAgent(
            processor=processor,
            llm_model_name=config.extractor.model if hasattr(config, 'extractor') else "mistralai/Mistral-7B-Instruct-v0.2",
            device=config.extractor.device if hasattr(config, 'extractor') else None,
            use_4bit=config.extractor.get('4bit', True) if hasattr(config, 'extractor') else True
        )
        
        # Execute query
        results = query_agent.query(
            query=query,
            top_k=limit,
            min_score=min_score
        )
        
        # Display results
        if results["success"]:
            print("\n" + "=" * 80)
            print("ANSWER:")
            print(results["answer"])
            print("=" * 80 + "\n")
            
            if verbose:
                print("\nExtracted Entities:")
                for entity_type, value in results["extracted_entities"].items():
                    print(f"  {entity_type}: {value}")
                
                print("\nVector Search Results:")
                for i, r in enumerate(results["vector_results"][:3]):  # Show only top 3 to keep output manageable
                    print(f"  Result {i+1} (Score: {r['score']:.2f}):")
                    print(f"  {r['content'][:200]}..." if len(r['content']) > 200 else f"  {r['content']}")
                    print()
                
                print("\nKnowledge Graph Results:")
                if results["knowledge_graph_results"]:
                    for i, kg_result in enumerate(results["knowledge_graph_results"][:5]):  # Show only top 5
                        print(f"  Entity {i+1}: {kg_result.get('type', 'Unknown')} - {kg_result.get('value', 'Unknown')}")
                        if 'document_id' in kg_result:
                            print(f"    Document: {kg_result['document_id']}")
                else:
                    print("  No specific entities found in knowledge graph.")
        else:
            print(f"Query failed: {results['error']}")
    else:
        # Use standard processor query
        logger.info(f"Executing standard query: {query}")
        results = processor.query(
            query=query,
            limit=limit
        )
        
        # Display results
        if results.get('success', False):
            print(f"Query returned {len(results.get('results', []))} results:")
            for i, result in enumerate(results.get('results', [])):
                print(f"\nResult {i+1} (Score: {result.get('similarity', 0):.2f}):")
                print(f"Document: {result.get('document_id', 'Unknown')}")
                content = result.get('content', '')
                print(f"Content: {content[:300]}..." if len(content) > 300 else f"Content: {content}")
        else:
            print(f"Query failed: {results.get('error', 'Unknown error')}")
    
    # Close processor resources if needed
    if hasattr(processor, 'close'):
        processor.close()

def main():
    """Main function to query the knowledge base."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Query the knowledge base")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--config", default=".env", help="Path to configuration file")
    parser.add_argument("--standard", action="store_true", help="Use standard query instead of RAG+KG")
    parser.add_argument("--verbose", action="store_true", help="Display verbose results")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results to return")
    parser.add_argument("--min-score", type=float, default=0.6, help="Minimum similarity score")
    args = parser.parse_args()
    
    # Load configuration
    config = get_config(args.config)
    setup_logging(config.logging.level)
    
    # Query knowledge base
    query_knowledge_base(
        query=args.query,
        config=config,
        use_advanced=not args.standard,
        verbose=args.verbose,
        limit=args.limit,
        min_score=args.min_score
    )

if __name__ == "__main__":
    main() 