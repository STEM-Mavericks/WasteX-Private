import os

# Generate a random secret key
secret_key = os.urandom(32).hex()

# Now you can use secret_key in your Flask app
print(secret_key)
