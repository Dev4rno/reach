import string
import random

def random_id():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=8))