#!/bin/bash

echo "🔄 Preparing n8n workflow for import..."

# Copy workflow file to container
echo "📁 Copying workflow file to container..."
docker cp n8n/workflows/resume-processing.json agent-n8n_n8n_1:/tmp/resume-processing.json

echo "✅ Workflow file ready for import!"
echo ""
echo "📋 Quick import steps (30 seconds):"
echo "1. Go to n8n at http://localhost:5678"
echo "2. Click 'Workflows' in the left sidebar"
echo "3. Click 'Import from File'"
echo "4. Select: n8n/workflows/resume-processing.json"
echo "5. Click 'Import' (overwrites existing)"
echo "6. Activate the workflow (toggle switch)"
echo "7. Save the workflow"
echo ""
echo "🎯 The workflow file is ready with the latest changes!"
