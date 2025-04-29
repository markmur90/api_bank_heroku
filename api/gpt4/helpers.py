# api/gpt4/helpers.py
import random
import string

def generate_unique_code(length=35):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
