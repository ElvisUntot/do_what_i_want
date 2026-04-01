"""
Examples for do_what_i_want()
Run directly to see what happens.
"""

from dwiw import do_what_i_want

people = [
    {"name": "Alice", "age": 30, "salary": 55000},
    {"name": "Bob",   "age": 25, "salary": 42000},
    {"name": "Carol", "age": 35, "salary": 67000},
    {"name": "Dave",  "age": 28, "salary": 38000},
]

# --- Example 1: AI solves directly ---
print("=== Example 1: AI solves directly ===")
result = do_what_i_want(
    "Sort by salary descending and return only name and salary",
    people,
    execute=False
)
print(result)

# --- Example 2: AI writes code, executed locally ---
print("\n=== Example 2: Code execution ===")
result = do_what_i_want(
    "Calculate the average salary and find the oldest person",
    people,
    execute=True
)
print(result)

# --- Example 3: Force a different backend ---
print("\n=== Example 3: Local backend ===")
result = do_what_i_want(
    "How many people earn more than 40000?",
    people,
    execute=False,
    backend="local"
)
print(result)

# --- Example 4: No data object, pure text task ---
print("\n=== Example 4: No data object ===")
result = do_what_i_want(
    "Explain in one sentence why Python is great"
)
print(result)
