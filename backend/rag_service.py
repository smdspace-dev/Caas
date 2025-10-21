import os
import openai
from typing import List, Dict, Any, Optional
from vector_service import VectorService
import time
import json

class RAGService:
    """Handle RAG (Retrieval-Augmented Generation) pipeline"""
    
    def __init__(self, vector_service: VectorService, use_openai: bool = False):
        self.vector_service = vector_service
        self.use_openai = use_openai
        
        if use_openai and os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.model = "gpt-3.5-turbo"
        else:
            # For demo purposes, we'll use a simple template-based response
            self.model = "template"
    
    def retrieve_context(self, query: str, chatbot_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context from vector database"""
        try:
            return self.vector_service.similarity_search(query, chatbot_id, top_k)
        except Exception as e:
            print(f"Error in context retrieval: {str(e)}")
            return []
    
    def build_prompt(self, query: str, context_chunks: List[Dict[str, Any]], chatbot_config: Dict[str, Any] = None) -> str:
        """Build prompt for the language model"""
        # Default chatbot configuration
        default_config = {
            "name": "AI Assistant",
            "tone": "friendly",
            "instructions": "You are a helpful AI assistant. Answer questions based on the provided context."
        }
        
        config = {**default_config, **(chatbot_config or {})}
        
        # Build context from retrieved chunks
        context_text = ""
        if context_chunks:
            context_text = "\n\n".join([chunk["text"] for chunk in context_chunks])
        
        # Build the prompt
        prompt = f"""You are {config['name']}, a {config['tone']} AI assistant.

{config['instructions']}

Context Information:
{context_text if context_text else "No relevant context found."}

User Question: {query}

Please provide a helpful and accurate answer based on the context provided. If the context doesn't contain enough information to answer the question, politely say so and provide general guidance if possible."""

        return prompt
    
    def generate_response_openai(self, prompt: str) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        try:
            start_time = time.time()
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            end_time = time.time()
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "response_time": end_time - start_time,
                "model": self.model
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble generating a response right now. Please try again later.",
                "tokens_used": 0,
                "response_time": 0
            }
    
    def generate_response_template(self, prompt: str, context_chunks: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Generate response using template (fallback when no OpenAI API)"""
        try:
            start_time = time.time()
            
            if context_chunks:
                # We have relevant context
                context_text = "\n\n".join([chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"] for chunk in context_chunks])
                
                response = f"""Based on the uploaded documents, here's what I found relevant to your question "{query}":

{context_text}

This information comes from {len(context_chunks)} relevant section(s) in your documents. The response is generated from your uploaded content to ensure accuracy and relevance to your specific materials."""
            else:
                response = f"""I don't have specific information about "{query}" in the uploaded documents. This could mean:

1. The topic isn't covered in the uploaded materials
2. The question might need to be phrased differently
3. More documents might need to be uploaded

Please try rephrasing your question or upload additional relevant documents to get better answers."""
            
            end_time = time.time()
            
            return {
                "success": True,
                "response": response,
                "tokens_used": len(response.split()),  # Rough estimate
                "response_time": end_time - start_time,
                "model": "template"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble processing your request right now.",
                "tokens_used": 0,
                "response_time": 0
            }
    
    def process_query(self, query: str, chatbot_id: str, chatbot_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process complete RAG query pipeline"""
        try:
            # Step 1: Retrieve relevant context
            context_chunks = self.retrieve_context(query, chatbot_id, top_k=5)
            
            # Step 2: Build prompt
            prompt = self.build_prompt(query, context_chunks, chatbot_config)
            
            # Step 3: Generate response
            if self.use_openai and os.getenv('OPENAI_API_KEY'):
                result = self.generate_response_openai(prompt)
            else:
                result = self.generate_response_template(prompt, context_chunks, query)
            
            # Step 4: Add context information to result
            result.update({
                "context_chunks": len(context_chunks),
                "context_sources": [chunk.get("metadata", {}).get("document_id") for chunk in context_chunks],
                "query": query,
                "chatbot_id": chatbot_id
            })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your question.",
                "tokens_used": 0,
                "response_time": 0,
                "context_chunks": 0,
                "query": query,
                "chatbot_id": chatbot_id
            }
    
    def get_chatbot_stats(self, chatbot_id: str) -> Dict[str, Any]:
        """Get statistics about the chatbot's knowledge base"""
        try:
            stats = self.vector_service.get_collection_stats(chatbot_id)
            return {
                "success": True,
                **stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_query(self, query: str = "What is this document about?", chatbot_id: str = "test") -> Dict[str, Any]:
        """Test the RAG pipeline with a sample query"""
        return self.process_query(query, chatbot_id)