from langchain_openai import ChatOpenAI
import json
import logging
from typing import List, Dict, Any

# Setup logger
logger = logging.getLogger(__name__)


def create_llm_client(
    model: str,
    temperature: float = 0,
    openai_api_key: str = None,
) -> ChatOpenAI:
    """Create and return a ChatOpenAI instance"""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=openai_api_key,
    )


# For backward compatibility, create an alias
OpenAIResponsesClient = create_llm_client


# =============================================================================
# RULE METADATA - Will be populated by individual agents
# =============================================================================

ALL_RULES = {}


def get_all_rule_names() -> List[str]:
    """Get list of all rule names"""
    return [rule_data["config"]["rule_name"] for rule_data in ALL_RULES.values()]


def add_new_rule_type(rule_key: str, config: Dict, rules: List[str], prompt_function):
    """
    Add a new rule type to the system

    Args:
        rule_key: Unique identifier for the rule type
        config: Rule configuration dictionary
        rules: List of rule descriptions
        prompt_function: Function that generates prompts for this rule type
    """
    ALL_RULES[rule_key] = {
        "config": config,
        "rules": rules,
        "prompt_function": prompt_function,
    }
