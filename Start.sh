#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    source .env
fi

# Stop any active ngrok agent sessions
./ngrok/ngrok kill

# Start ngrok with authentication token
./ngrok/ngrok authtoken $NGROK_AUTH_TOKEN

# Check if authentication failed
if [ $? -ne 0 ]; then
    echo "Error: Authentication failed with ngrok."
    exit 1
fi

# Start ngrok HTTP tunnel
./ngrok/ngrok http $FORWARD_PORT &

# Wait for ngrok to initialize and fetch the URL
sleep 5  # Adjust the sleep duration based on ngrok startup time

# Get the ngrok URL from ngrok's status API without jq
ngrok_response=$(curl -s http://localhost:4040/api/tunnels)

# Parse ngrok URL without jq
ngrok_url=$(echo "$ngrok_response" | grep -o '"public_url":"[^"]*' | cut -d '"' -f 4)

# Check if ngrok URL is empty
if [ -z "$ngrok_url" ]; then
    echo "Error: Ngrok URL not found. Ngrok might not have properly started or created tunnels."
    exit 1
fi

# # Save the ngrok URL to a file
# echo "$ngrok_url" > ngrok_url.txt

echo "Ngrok URL: $ngrok_url"

# Update specific variable in .env file
sed -i "s|TELEGRAM_APP_URL=.*|TELEGRAM_APP_URL=$ngrok_url|" .env

# Run docker-compose
docker-compose up -d
