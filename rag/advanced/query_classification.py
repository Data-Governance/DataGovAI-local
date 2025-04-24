"""Query classification and routing for the RAG system.

This module provides functionality to classify user queries into different types
and route them to appropriate processing pipelines.
"""

import re
from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI

class QueryType(Enum):
    """Enum representing the different types of queries."""
    
    GRS_RELATED = "grs_related"  # Queries about General Records Schedules
    FOLLOWUP = "followup"        # Follow-up questions referring to previous conversation
    GENERAL = "general"          # General questions not requiring RAG retrieval
    UNKNOWN = "unknown"          # Unclassified/ambiguous queries

@dataclass
class ClassificationResult:
    """Result of query classification."""
    
    query: str                      # Original query text
    query_type: QueryType           # Classified query type
    confidence: float               # Classification confidence score (0.0-1.0)
    sub_type: Optional[str] = None  # Optional sub-classification (e.g., category within GRS)
    reasoning: Optional[str] = None # Optional explanation for classification

class QueryClassifier:
    """Classifies queries into different types.
    
    This class uses a combination of keyword matching, semantic classification,
    and conversation context analysis to classify user queries.
    """
    
    def __init__(
        self, 
        llm: Optional[LLM] = None,
        domain_keywords: Optional[List[str]] = None,
        classification_threshold: float = 0.75
    ):
        """Initialize the query classifier.
        
        Args:
            llm: LLM for semantic classification (optional)
            domain_keywords: List of domain-specific keywords (optional)
            classification_threshold: Threshold for classification confidence
        """
        self.llm = llm or OpenAI(model="gpt-3.5-turbo-0125", temperature=0.1)
        
        # Default domain keywords if none provided
        self.domain_keywords = domain_keywords or [
            "retention", "schedule", "records", "document", "archive", 
            "compliance", "regulatory", "disposition", "storage", 
            "grs", "general records", "retention schedule"
        ]
        
        self.classification_threshold = classification_threshold
        
        # Follow-up indicators (pronouns, demonstratives, etc.)
        self.followup_indicators = [
            "it", "they", "them", "those", "that", "these", "this", "the",
            "previous", "earlier", "above", "mentioned"
        ]
    
    def classify(self, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> ClassificationResult:
        """Classify the query into a specific type.
        
        Args:
            query: The user query text
            conversation_history: Optional list of previous conversation turns
                Each item should be a dict with 'role' and 'content' keys
        
        Returns:
            ClassificationResult with classified type and confidence
        """
        # 1. Check if it's a follow-up question based on conversation history
        if self._is_followup(query, conversation_history):
            return ClassificationResult(
                query=query,
                query_type=QueryType.FOLLOWUP,
                confidence=0.9,  # High confidence for follow-up detection
                reasoning="Query appears to be a follow-up to previous conversation"
            )
        
        # 2. Check for domain-specific keywords (GRS-related)
        keyword_match = self._has_domain_keywords(query)
        if keyword_match:
            return ClassificationResult(
                query=query,
                query_type=QueryType.GRS_RELATED,
                confidence=0.85,  # High confidence for keyword matches
                reasoning=f"Query contains domain-specific keywords: {keyword_match}"
            )
        
        # 3. Use LLM for more nuanced classification
        return self._classify_with_llm(query)
    
    def _is_followup(self, query: str, conversation_history: Optional[List[Dict[str, Any]]]) -> bool:
        """Determine if the query is a follow-up question.
        
        Args:
            query: User query
            conversation_history: List of previous conversation turns
        
        Returns:
            True if the query appears to be a follow-up, False otherwise
        """
        if not conversation_history or len(conversation_history) == 0:
            return False
        
        query_lower = query.lower()
        query_tokens = query_lower.split()
        
        # Check for follow-up indicators (pronouns, etc.)
        if any(token in self.followup_indicators for token in query_tokens):
            return True
        
        # Very short queries are likely follow-ups
        if len(query_tokens) <= 3 and not query_lower.endswith("?"):
            return True
        
        # If the query starts with a verb, it might be a follow-up
        if query_tokens and query_tokens[0] in ["is", "are", "does", "do", "can", "could", "would", "will", "has", "have"]:
            return True
            
        return False
    
    def _has_domain_keywords(self, query: str) -> List[str]:
        """Check if the query contains domain-specific keywords.
        
        Args:
            query: User query
        
        Returns:
            List of matched keywords, empty if none found
        """
        query_lower = query.lower()
        return [keyword for keyword in self.domain_keywords if keyword.lower() in query_lower]
    
    def _classify_with_llm(self, query: str) -> ClassificationResult:
        """Use LLM to classify the query.
        
        Args:
            query: User query
        
        Returns:
            ClassificationResult with LLM-based classification
        """
        prompt = f"""
        Determine if the following query is related to General Records Schedules (GRS), 
        document management, or records retention policies.
        
        Query: "{query}"
        
        Classify the query into one of these categories:
        1. GRS_RELATED - Questions about document retention, schedules, or records management
        2. GENERAL - General questions not related to records management
        
        Respond with the category name followed by a confidence score between 0 and 1,
        then a brief explanation. Format: "CATEGORY|CONFIDENCE|EXPLANATION"
        
        Example: "GRS_RELATED|0.95|Question explicitly mentions retention schedules"
        Example: "GENERAL|0.85|General question about weather with no relation to records"
        """
        
        try:
            response = self.llm.complete(prompt).text.strip()
            parts = response.split("|")
            
            if len(parts) >= 2:
                category = parts[0].strip()
                confidence = float(parts[1].strip())
                reasoning = parts[2].strip() if len(parts) > 2 else None
                
                if category == "GRS_RELATED" and confidence >= self.classification_threshold:
                    return ClassificationResult(
                        query=query,
                        query_type=QueryType.GRS_RELATED,
                        confidence=confidence,
                        reasoning=reasoning
                    )
                else:
                    return ClassificationResult(
                        query=query,
                        query_type=QueryType.GENERAL,
                        confidence=confidence,
                        reasoning=reasoning
                    )
            else:
                # Fallback if LLM response format is incorrect
                return ClassificationResult(
                    query=query,
                    query_type=QueryType.GENERAL,
                    confidence=0.5,
                    reasoning="Default classification due to processing error"
                )
        except Exception as e:
            # Fallback for any LLM errors
            return ClassificationResult(
                query=query,
                query_type=QueryType.UNKNOWN,
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}"
            )

class QueryRouter:
    """Routes queries to appropriate processing pipelines based on their classification.
    
    This class takes a ClassificationResult and determines which processing
    pipeline should handle the query.
    """
    
    def __init__(self):
        """Initialize the query router."""
        pass
    
    def route(self, classification_result: ClassificationResult) -> Dict[str, Any]:
        """Route the query to the appropriate pipeline.
        
        Args:
            classification_result: The result from QueryClassifier
        
        Returns:
            Dict with routing information including:
                - pipeline: The pipeline to use ('rag', 'conversational', 'direct')
                - requires_retrieval: Whether document retrieval is needed
                - requires_context: Whether conversation context is needed
        """
        if classification_result.query_type == QueryType.GRS_RELATED:
            return {
                "pipeline": "rag",
                "requires_retrieval": True,
                "requires_context": False,
                "filter_metadata": {}  # Could include category filters for more specific queries
            }
        elif classification_result.query_type == QueryType.FOLLOWUP:
            return {
                "pipeline": "conversational",
                "requires_retrieval": True,  # May need retrieval based on context
                "requires_context": True,
                "filter_metadata": {}
            }
        elif classification_result.query_type == QueryType.GENERAL:
            return {
                "pipeline": "direct",
                "requires_retrieval": False,
                "requires_context": False,
                "filter_metadata": {}
            }
        else:
            # Default fallback for unknown queries
            return {
                "pipeline": "direct",
                "requires_retrieval": False,
                "requires_context": False,
                "filter_metadata": {}
            } 