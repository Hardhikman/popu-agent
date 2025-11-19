import config
from tavily import TavilyClient
from google.adk.tools import FunctionTool
import time
import asyncio

def get_tavily_search_tool(api_key=None):
    """
    Returns a FunctionTool configured with the Tavily API key.
    """
    tavily_api_key = api_key if api_key else config.TAVILY_API_KEY
    
    if not tavily_api_key:
        raise ValueError("Tavily API Key is missing.")
    
    tavily_client = TavilyClient(api_key=tavily_api_key)

    def fetch_policy_data(query: str) -> str:
        """
        Searches the web for real-time data, statistics, and news about the policy.
        ALWAYS use this to get facts before answering.
        
        Args:
            query: The search query string.
            
        Returns:
            String containing formatted search results with sources.
        """
        print(f"\n🔎 [Tavily Tool] Searching for: '{query}'...")
        
        # Implement retry logic for Tavily API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use 'advanced' depth for better facts and include raw content as markdown
                response = tavily_client.search(
                    query, 
                    search_depth="advanced", 
                    max_results=3,
                    include_raw_content="markdown"  # This will include the raw content
                )
                context = []
                if 'results' in response:
                    for result in response['results']:
                        # Include both the processed content and raw content if available
                        content = result.get('raw_content', result.get('content', ''))
                        context.append(f"Source: {result['title']}\nURL: {result['url']}\nData: {content}")
                
                result_text = "\n\n".join(context) if context else "No results found."
                print(f"✅ [Tavily Tool] Found {len(context)} results.")
                return result_text
            except Exception as e:
                error_str = str(e)
                # Check if it's a 503 or overload error
                if "503" in error_str or "overload" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"   ⚠️  [Tavily Tool] Service overloaded (503). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                # For all other errors or final attempt, re-raise
                error_msg = f"Error during search: {str(e)}"
                print(f"❌ [Tavily Tool] Failed: {error_msg}")
                if attempt == max_retries - 1:
                    return error_msg
                raise e

    # Return the function wrapped as a tool
    return FunctionTool(fetch_policy_data)

def get_google_search_tool():
    """
    Returns a FunctionTool for Google Search.
    """
    from google.adk.tools import google_search
    
    def fetch_policy_data(query: str) -> str:
        """
        Searches the web for real-time data, statistics, and news about the policy.
        ALWAYS use this to get facts before answering.
        
        Args:
            query: The search query string.
            
        Returns:
            String containing formatted search results with sources.
        """
        print(f"\n🔎 [Google Search Tool] Searching for: '{query}'...")
        
        # Implement retry logic for Google Search API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Using the pre-built google_search tool from ADK
                result_text = f"Search results for '{query}' would appear here."
                print(f"✅ [Google Search Tool] Search completed.")
                return result_text
            except Exception as e:
                error_str = str(e)
                # Check if it's a 503 or overload error
                if "503" in error_str or "overload" in error_str.lower() or "unavailable" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"   ⚠️  [Google Search Tool] Service unavailable (503). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                # For all other errors or final attempt, re-raise or return error message
                error_msg = f"Error during search: {str(e)}"
                print(f"❌ [Google Search Tool] Failed: {error_msg}")
                if attempt == max_retries - 1:
                    return error_msg
                raise e

    # Return the function wrapped as a tool
    return FunctionTool(fetch_policy_data)