import numpy as np
import random
import random

# Generate a list of 9 unique random numbers (excluding 1)
random_weeks = random.sample(range(1, 16), 9)

# Add 1 at the start of the list
random_weeks.insert(0, 0)

# Optionally, sort the list to maintain sequential order
random_weeks.sort()

print(random_weeks)

index = 3
number_at_index = random_weeks[index]

print(f"Number at index {index}: {number_at_index}")