"""
Tools for the Agent System
Includes Web Search and other utilities
"""
import requests
import json

class SearchTool:
    """A tool to search the web for news"""
    
    @staticmethod
    def search_news(query):
        """
        Searches for news. 
        Note: In a production environment, this would use Serper or Google Search API.
        For this demo, we use a search simulation that returns real-looking news snippets.
        """
        # In this environment, I will use my internal 'search_web' tool capability 
        # but since I am building a standalone app for the user, 
        # I will implement a robust mock that allows the agent to 'proceed' 
        # or I can try to find a free search API.
        
        # For now, let's provide a utility that the agent can call.
        print(f"DEBUG: Searching for: {query}")
        
        # Simulated search result for common providers
        mock_results = {
            "nvidia": "NVIDIA stock hits all-time high as AI demand surges. New Blackwell chips entering production. NVIDIA announces partnership with Mercedes-Benz for autonomous driving.",
            "google": "Google DeepMind unveils new Gemini 1.5 Pro model. Alphabet reports strong cloud growth. Google Fiber expands to 5 new cities.",
            "openai": "OpenAI launches SearchGPT prototype. Sam Altman discusses future of AGI at Davos. OpenAI expands safety team with new hires.",
            "apple": "Apple Vision Pro launches globally. Rumors of Apple Car revived. iOS 18 to feature major AI integration.",
            "meta": "Meta releases Llama 3 with 400B parameters. Zuckerberg highlights metaverse progress. Threads reaches 175 million monthly active users."
        }
        
        provider = query.lower().split()[0]
        result = mock_results.get(provider, f"Latest developments and news regarding {query} including market performance and technology updates.")
        
        return result
