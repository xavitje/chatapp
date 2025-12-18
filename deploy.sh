#!/bin/bash
# deploy.sh - Complete deployment script for chat.drissi.store

echo "🚀 Starting deployment..."

# Stop and remove old container
echo "🛑 Stopping old container..."
sudo docker rm -f chatapp

# Build new image
echo "🏗️  Building Docker image..."
sudo docker build -t chatapp-image .

# Run new container
echo "▶️  Starting new container..."
sudo docker run -d \
  --name chatapp \
  -p 127.0.0.1:8080:5000 \
  -v chatapp-data:/app/data \
  --restart always \
  chatapp-image

# Check if container is running
echo "✅ Checking container status..."
sudo docker ps | grep chatapp

echo "📋 Container logs:"
sudo docker logs chatapp --tail 20

echo ""
echo "✅ Deployment complete!"
echo "🌐 App should be available at: https://chat.drissi.store"
echo ""
echo "📝 Useful commands:"
echo "  View logs: sudo docker logs -f chatapp"
echo "  Restart: sudo docker restart chatapp"
echo "  Stop: sudo docker stop chatapp"
