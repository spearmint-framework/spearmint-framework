# import asyncio
# import spearmint as mint
# from experiments import llm_extraction_exp, parse_document_exp

# hypothesis = mint.Hypothesis()
# hypothesis.configure("config.yaml")
# hypothesis.add_service(AzureOpenAIClient)
# hypothesis.add_experiment(llm_extraction_exp, name="llm_extraction")
# hypothesis.add_experiment(parse_document_exp, name="parse_document")

# @mint.cli(hypothesis)
# async def main(experiment: mint.Experiment, config: dict) -> None:
#     await hypothesis.run(experiment, config=config)

# if __name__ == "__main__":
#     asyncio.run(main())

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from spearmint.hypothesis import Hypothesis
from spearmint.config import DynamicValue


@pytest.mark.asyncio
async def test_hypothesis_run_static_config_calls_experiment_exactly_once():
    """Test that hypothesis.run calls the experiment function exactly once."""
    # Create a mock experiment function
    mock_experiment = AsyncMock(return_value="test_result")
    
    # Create a Hypothesis instance
    hypothesis = Hypothesis()
    
    # Run the experiment
    config = {"param": "value"}
    result = await hypothesis.run(mock_experiment, config=config)
    
    # Verify the experiment function was called exactly once
    mock_experiment.assert_called_once_with(**config)
    
    # Verify the result is returned
    assert result == ["test_result"]

@pytest.mark.asyncio
async def test_hypothesis_run_dynamic_config_calls_experiment_multiple_times():
    """Test that hypothesis.run calls the experiment function multiple times with different configurations."""
    # Create a mock experiment function
    mock_experiment = AsyncMock(return_value="test_result")
    
    # Create a Hypothesis instance
    hypothesis = Hypothesis()
    
    config = {
        "param": DynamicValue(["value1", "value2"])
    }
    
    # Run the experiment
    result = await hypothesis.run(mock_experiment, config=config)
    
    # Verify the experiment function was called twice with different configurations
    assert mock_experiment.call_count == 2
    mock_experiment.assert_any_call(param="value1")
    mock_experiment.assert_any_call(param="value2")
    
    # Verify the result is returned from the last call
    assert result == ["test_result", "test_result"]


@pytest.mark.asyncio
async def test_hypothesis_run_multiple_dynamic_config_calls_experiment_multiple_times():
    """Test that hypothesis.run calls the experiment function multiple times with different configurations."""
    # Create a mock experiment function
    mock_experiment = AsyncMock(return_value="test_result")
    
    # Create a Hypothesis instance
    hypothesis = Hypothesis()
    
    config = {
        "param1": DynamicValue(["value1", "value2"]),
        "param2": DynamicValue(range(3, 5))
    }
    
    # Run the experiment
    result = await hypothesis.run(mock_experiment, config=config)
    
    # Verify the experiment function was called twice with different configurations
    assert mock_experiment.call_count == 4
    mock_experiment.assert_any_call(param1="value1", param2=3)
    mock_experiment.assert_any_call(param1="value2", param2=3)
    mock_experiment.assert_any_call(param1="value1", param2=4)
    mock_experiment.assert_any_call(param1="value2", param2=4)
    
    # Verify the result is returned from the last call
    assert result == ["test_result", "test_result", "test_result", "test_result"]