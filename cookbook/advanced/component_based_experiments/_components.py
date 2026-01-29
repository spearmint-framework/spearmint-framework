import random

# Define some simple search components for demonstration purposes
SEARCH_DATABASE = {
    "The quick brown fox jumps over the lazy dog",
    "A journey of a thousand miles begins with a single step",
    "To be or not to be, that is the question",
    "All that glitters is not gold",
    "I think, therefore I am",
    "The only thing we have to fear is fear itself",
    "Ask not what your country can do for you; ask what you can do for your country",
}

def random_search(query: str) -> list[str]:
    k = random.randint(1, len(SEARCH_DATABASE))
    return random.sample(list(SEARCH_DATABASE), k=k)

def simple_search(query: str) -> list[str]:
    return [
        item for item in SEARCH_DATABASE if query.lower() in item.lower()
    ]

def vector_search(query: str) -> list[str]:
    # Placeholder for a vector-based search implementation
    return [
        item for item in SEARCH_DATABASE if len(item) % 2 == len(query) % 2
    ]

# Define some simple ranking components for demonstration purposes
def noop_rank(results: list[str], k: int) -> list[str]:
    return results[:k]

def length_rank(results: list[str], k: int) -> list[str]:
    return sorted(results, key=len, reverse=True)[:k]

def alphabetical_rank(results: list[str], k: int) -> list[str]:
    return sorted(results)[:k]