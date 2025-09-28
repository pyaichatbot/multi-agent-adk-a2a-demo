#!/bin/bash
# deploy.sh - Deploy all services to Google Cloud Run

set -e

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"

echo "Deploying Enterprise Multi-Agent System to Google Cloud Run..."

# Deploy MCP Server
echo "Deploying MCP Server..."
gcloud run deploy mcp-server \
  --source ./mcp-server \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 100 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

# Get MCP Server URL
MCP_URL=$(gcloud run services describe mcp-server --region=$REGION --format='value(status.url)')

# Deploy Data Search Agent
echo "Deploying Data Search Agent..."
gcloud run deploy data-search-agent \
  --source ./data-search-agent \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 5 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars MCP_SERVER_URL=$MCP_URL

# Deploy Reporting Agent
echo "Deploying Reporting Agent..."
gcloud run deploy reporting-agent \
  --source ./reporting-agent \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 50 \
  --max-instances 5 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars MCP_SERVER_URL=$MCP_URL

# Get agent URLs
DATA_AGENT_URL=$(gcloud run services describe data-search-agent --region=$REGION --format='value(status.url)')
REPORTING_AGENT_URL=$(gcloud run services describe reporting-agent --region=$REGION --format='value(status.url)')

# Deploy Orchestrator Agent (needs agent URLs)
echo "Deploying Orchestrator Agent..."
gcloud run deploy orchestrator-agent \
  --source ./orchestrator-agent \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --concurrency 50 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars MCP_SERVER_URL=$MCP_URL \
  --set-env-vars DATA_AGENT_URL=$DATA_AGENT_URL \
  --set-env-vars REPORTING_AGENT_URL=$REPORTING_AGENT_URL

echo "Deployment complete!"
echo "MCP Server: $MCP_URL"
echo "Data Search Agent: $DATA_AGENT_URL"
echo "Reporting Agent: $REPORTING_AGENT_URL"
ORCHESTRATOR_URL=$(gcloud run services describe orchestrator-agent --region=$REGION --format='value(status.url)')
echo "Orchestrator: $ORCHESTRATOR_URL"
