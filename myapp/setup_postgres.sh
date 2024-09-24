#!/bin/bash

# Update and install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo service postgresql start

# Switch to the postgres user
sudo -i -u postgres << EOF

# Create a new PostgreSQL role (user)
psql -c "CREATE USER myuser WITH PASSWORD 'mypassword';"

# Create a new database
psql -c "CREATE DATABASE mydb;"

# Grant privileges to the user on the database
psql -c "GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;"

# Exit postgres user
exit
EOF

echo "PostgreSQL setup complete."
