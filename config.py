import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API Keys from environment or set them directly here
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Default System Configuration
DEFAULT_POLICY_TOPIC = "Implementation of Universal Basic Income (UBI) in developing economies"
OUTPUT_FILENAME = "policy_report.md"

if not GOOGLE_API_KEY or not TAVILY_API_KEY:
    print("WARNING: API Keys are missing. Please set GOOGLE_API_KEY and TAVILY_API_KEY.")