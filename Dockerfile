FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-api.txt

# Copy package files
COPY mcp_flight_search/ ./mcp_flight_search/
COPY main.py pyproject.toml README.md LICENSE api_wrapper.py ./

# Install the package
RUN pip install -e .

# Expose the port
EXPOSE 8000

# Run the FastAPI microservice
CMD ["python", "api_wrapper.py"] 