#!/bin/bash

# Quick deployment script for the legal search microservice

echo "Deploying Legal Search Microservice..."

# Step 1: Build the API container
echo "Building API container..."
docker build -f Dockerfile -t legal-search-api:latest .

# Step 2: Run the container
echo "Starting API container..."
docker run -d \
  --name legal-search-api \
  -p 8000:8000 \
  -e SERP_API_KEY=$SERP_API_KEY \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  legal-search-api:latest

echo "Legal Search API is running on http://localhost:8000"
echo "Health Check: http://localhost:8000/api/legal/health"

# Test the API
echo "Testing API..."
sleep 5

curl -X POST "http://localhost:8000/api/legal/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_text": "This Employment Agreement is entered into between TechCorp Inc. and John Smith for the position of Software Engineer in California."
  }' | python -m json.tool

echo "🎉 Deployment complete! You can now integrate this API into your existing application."
