from datetime import datetime
import random


class Userdata:
    def generate_random_username(self):
        adjectives = ['Cool', 'Epic', 'Awesome', 'Brave', 'Swift', 'Silent', 'Mystic', 'Rapid', 'Clever', 'Bold']
        nouns = ['Gamer', 'Wolf', 'Phoenix', 'Dragon', 'Ninja', 'Warrior', 'Knight', 'Eagle', 'Shadow', 'Titan']
        numbers = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        return f"{random.choice(adjectives)}{random.choice(nouns)}{numbers}"

    def generate_random_password(self, length=12):
        characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+'
        return ''.join(random.choice(characters) for _ in range(length))

    def generate_random_birthdate(self):
        current_year = datetime.now().year
        birth_year = random.randint(1980, current_year - 18)
        birth_month = random.randint(1, 12)
        
        if birth_month in [1, 3, 5, 7, 8, 10, 12]:
            birth_day = random.randint(1, 31)
        elif birth_month in [4, 6, 9, 11]:
            birth_day = random.randint(1, 30)
        else:  # February
            birth_day = random.randint(1, 28)
        
        return birth_year, birth_month, birth_day