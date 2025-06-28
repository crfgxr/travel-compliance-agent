import pytest
import os
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Set test environment variables
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not set - skipping tests that require API access")
