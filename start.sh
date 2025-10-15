#!/bin/bash

echo "🚀 Starting n8n AI Hiring Agent..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker is running"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p sample_data
mkdir -p n8n/workflows
mkdir -p n8n/nodes

# Start services
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to initialize..."
sleep 15

# Check service health
echo "🔍 Checking service health..."
services=("postgres" "ollama" "text-extract" "embeddings" "n8n" "web")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is not running"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo ""
    echo "🎉 All services are running!"
    echo "=================================="
    echo "🌐 Web Application: http://localhost:3000"
    echo "🤖 n8n Workflows: http://localhost:5678"
    echo "📡 Text Extraction: http://localhost:8001"
    echo "🧠 Embeddings API: http://localhost:8002"
    echo "🗄️  Database: localhost:5432 (postgres/password)"
    echo ""
    echo "🔐 n8n Login Credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "📋 Demo Workflow:"
    echo "1. Go to http://localhost:3000"
    echo "2. Start with the 'AI Agent' tab to create autonomous goals"
    echo "3. Upload sample resumes from sample_data/ folder"
    echo "4. View workflows in the 'n8n Workflows' tab"
    echo "5. Open n8n editor at http://localhost:5678 to see the visual workflows"
    echo ""
    echo "📊 Sample data available in:"
    echo "- sample_data/sample_resume_1.txt (Python Developer)"
    echo "- sample_data/sample_resume_2.txt (Full Stack Developer)"
    echo "- sample_data/sample_resume_3.txt (DevOps Engineer)"
    echo "- sample_data/sample_jd.txt (Sample Job Description)"
    echo ""
    echo "🔧 To stop services: docker-compose down"
    echo "📝 To view logs: docker-compose logs -f"
    echo "🔄 To restart n8n: docker-compose restart n8n"
else
    echo ""
    echo "❌ Some services failed to start. Check logs with:"
    echo "docker-compose logs"
fi
