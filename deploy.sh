#!/bin/bash
set -e

# Configuration
GIT_REPO_DIR="$HOME/git/alma"
PRODUCTION_DIR="$HOME/production/projects/alma"

echo "🚀 Starting Alma deployment..."

# Step 1: Pull latest code
echo "📥 Pulling latest code from git..."
cd "$GIT_REPO_DIR"
git pull

# Step 2: Copy docker-compose.yml to production
echo "📋 Copying docker-compose.yml to production..."
cp "$GIT_REPO_DIR/docker-compose.yml" "$PRODUCTION_DIR/docker-compose.yml"

# Step 3: Build new image
echo "🔨 Building Docker image..."
cd "$PRODUCTION_DIR"
docker-compose build --no-cache

# Step 4: Deploy with zero-downtime restart
echo "🔄 Restarting container..."
docker-compose up -d

# Step 5: Show status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "📝 Recent logs:"
docker-compose logs --tail=20 alma
