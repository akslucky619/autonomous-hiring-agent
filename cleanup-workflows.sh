#!/bin/bash

echo "🧹 Cleaning up duplicate workflows..."

# Get list of workflow IDs
WORKFLOW_IDS=$(docker-compose exec -T n8n n8n list:workflow | grep "Resume Processing Pipeline" | cut -d'|' -f1)

echo "Found Resume Processing Pipeline workflows: $WORKFLOW_IDS"

# Delete all Resume Processing Pipeline workflows
for id in $WORKFLOW_IDS; do
    echo "Deleting workflow ID: $id"
    docker-compose exec -T n8n n8n delete:workflow --id=$id
done

echo "✅ Cleanup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Import the workflow fresh: ./update-workflow.sh"
echo "2. Activate the single workflow in n8n UI"
echo "3. Test the webhook"
