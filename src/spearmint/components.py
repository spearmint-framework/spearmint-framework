"""Components for the Spearmint framework.

This module contains various components that can be used in Spearmint experiments,
such as prompt templates, LLM integrations, etc.
"""
from typing import Any, Dict, Type, TypeVar, Union

T = TypeVar('T')

def prompt_from_file(variables: Dict[str, Any]) -> str:
    """Load a prompt template from a file and fill in variables.
    
    Args:
        variables: Dictionary of variables to substitute in the prompt
        
    Returns:
        The filled prompt as a string
    """
    # In a real implementation, this would load from a file
    # For demonstration, we'll just return a placeholder
    document = variables.get("document", "")
    return f"""Extract all company names mentioned in the document.
    
Document: {document}

Return a JSON with the following structure:
{{
    "companies": [
        "Company Name 1",
        "Company Name 2",
        ...
    ]
}}
"""

def structured_chat_completion(prompt: str, output_type: Type[T]) -> T:
    """Send a prompt to a chat model and parse the response.
    
    Args:
        prompt: The prompt to send to the chat model
        output_type: The type to parse the response as
        
    Returns:
        The parsed response
    """
    # In a real implementation, this would call an LLM API
    # For demonstration, we'll just return a placeholder
    # Normally this would also use the output_type for parsing
    return {"companies": ["Example Company 1", "Example Company 2"]}