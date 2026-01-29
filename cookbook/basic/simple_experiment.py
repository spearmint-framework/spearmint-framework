from spearmint import Spearmint, Config

# Initialize Spearmint with a single configuration
mint = Spearmint(configs=[{"model": "gpt-4", "temperature": 0.7}])

@mint.experiment()
def generate_text(prompt: str, config: Config) -> str:
    # The config is automatically injected based on the context
    print(f"Executing with config: {config}")
    return f"Processed '{prompt}' using {config['model']} (temp={config['temperature']})"

if __name__ == "__main__":
    # Use the run context manager to handle the experiment execution
    with Spearmint.run(generate_text) as runner:
        result = runner("Hello, World!")
        print(f"Result: {result.main_result.result}")
        assert result.main_result.result == "Processed 'Hello, World!' using gpt-4 (temp=0.7)"
