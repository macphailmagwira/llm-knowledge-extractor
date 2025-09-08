#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Starting FastAPI application entrypoint script..."

# Required environment variables
REQUIRED_VARS=(
  "ENVIRONMENT"
  "APP_TITLE"
  "DEBUG"
  "ALLOWED_HOST"
  "SECRET_KEY"
  "POSTGRES_USER"
  "POSTGRES_PASSWORD"
  "POSTGRES_DB"
  "POSTGRES_PORT"
  "POSTGRES_HOST"
  "DB_URL"
  "AZURE_OPENAI_GPT_4O_ENDPOINT"
  "AZURE_OPENAI_GPT_4O_API_KEY"
  "AZURE_OPENAI_GPT_4O_DEPLOYMENT_NAME"
  "AZURE_OPENAI_GPT_4O_MODEL_NAME"
  "AZURE_OPENAI_GPT_4O_API_VERSION"
)


# Optional environment variables
OPTIONAL_VARS=(
  "PORT"                        # Use default if not provided
  "HOST"                        # Use default if not provided
  "LOG_LEVEL"                   # Use default if not provided
  "WORKERS"                     # Use default if not provided  
)

# Function to check if a variable is set
check_env_var() {
  local var_name="$1"
  if [ -z "${!var_name}" ]; then
    return 1
  fi
  return 0
}

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  # Safely load environment variables, handling empty lines and comments
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$line" ]] && continue
    
    # Extract variable and value, handling quotes and spaces around =
    if [[ "$line" =~ ^[[:space:]]*([^[:space:]=#]+)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      # Remove trailing whitespace
      value=$(echo "$value" | sed 's/[[:space:]]*$//')
      # Remove quotes if present
      value="${value%\"}"
      value="${value#\"}"
      value="${value%\'}"
      value="${value#\'}"
      # Export the variable
      export "$key=$value"
    fi
  done < .env
fi

# Check required environment variables
missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
  if ! check_env_var "$var"; then
    missing_vars+=("$var")
  fi
done

# Report missing required variables
if [ ${#missing_vars[@]} -gt 0 ]; then
  echo -e "${RED}Error: Missing required environment variables:${NC}"
  for var in "${missing_vars[@]}"; do
    echo -e "${RED}- $var${NC}"
  done
  exit 1
else
  echo -e "${GREEN}All required environment variables are set${NC}"
fi

# Check optional environment variables
missing_optional=()
for var in "${OPTIONAL_VARS[@]}"; do
  if ! check_env_var "$var"; then
    missing_optional+=("$var")
  fi
done

# Report missing optional variables
if [ ${#missing_optional[@]} -gt 0 ]; then
  echo -e "${YELLOW}Warning: Missing optional environment variables:${NC}"
  for var in "${missing_optional[@]}"; do
    echo -e "${YELLOW}- $var${NC}"
  done
fi

# Set default values for optional variables if not present
PORT=${PORT:-11000}
HOST=${HOST:-"0.0.0.0"}
LOG_LEVEL=${LOG_LEVEL:-"debug"}

# Set reload flag based on DEBUG environment variable
if [ "${DEBUG}" = "True" ] || [ "${DEBUG}" = "true" ] || [ "${DEBUG}" = "1" ]; then
  DEBUG_FLAG="--reload"
else
  DEBUG_FLAG=""
fi

echo -e "${GREEN}Environment validation completed successfully!${NC}"
echo -e "Starting FastAPI application with:"
echo -e "  - Host: ${HOST}"
echo -e "  - Port: ${PORT}"
echo -e "  - Workers: ${WORKERS}"
echo -e "  - Log level: ${LOG_LEVEL}"


# Start the FastAPI application using uvicorn with the llm_knowledge_extractor module
exec uvicorn llm_knowledge_extractor.main:app --host ${HOST} --port ${PORT} --log-level ${LOG_LEVEL} ${DEBUG_FLAG}