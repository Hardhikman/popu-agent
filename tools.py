import config
from tavily import TavilyClient
from google.adk.tools import FunctionTool

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
        try:
            # Use 'advanced' depth for better facts
            response = tavily_client.search(query, search_depth="advanced", max_results=3)
            context = []
            if 'results' in response:
                for result in response['results']:
                    context.append(f"Source: {result['title']}\nURL: {result['url']}\nData: {result['content']}")
            
            result_text = "\n\n".join(context) if context else "No results found."
            print(f"✅ [Tavily Tool] Found {len(context)} results.")
            return result_text
        except Exception as e:
            error_msg = f"Error during search: {str(e)}"
            print(f"❌ [Tavily Tool] Failed: {error_msg}")
            return error_msg

    # Return the function wrapped as a tool
    return FunctionTool(fetch_policy_data)