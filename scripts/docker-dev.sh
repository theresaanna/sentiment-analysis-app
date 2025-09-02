#!/bin/bash
# scripts/docker-dev.sh
# Development Docker setup script

set -e

echo "🚀 Starting Instagram Sentiment Analysis App (Development Mode)"
echo "=============================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual configuration!"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs/{flask,celery,nginx}
mkdir -p ssl
mkdir -p nginx/sites-available

# Stop any running containers
echo "🛑 Stopping any running containers..."
docker-compose down --remove-orphans

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

# Show logs for debugging
echo "📋 Service status:"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Redis: localhost:6379"
echo "Flower (monitoring): http://localhost:5555"

# Test API endpoint
echo "🧪 Testing API..."
sleep 5
curl -f http://localhost:8000/health || echo "⚠️ API not ready yet, please wait..."

echo "✅ Development environment is ready!"
echo "📊 Access Celery monitoring at: http://localhost:5555"
echo "🔗 API documentation available at the backend root endpoint"

# ================================
# scripts/docker-prod.sh
#!/bin/bash
# Production Docker setup script

set -e

echo "🚀 Starting Instagram Sentiment Analysis App (Production Mode)"
echo "=============================================================="

# Check if required files exist
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create it from .env.example"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs/{flask,celery,nginx}
mkdir -p ssl

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose pull

# Build and start production services
echo "🔨 Building and starting production services..."
docker-compose --profile production up --build -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check health
echo "🏥 Checking service health..."
docker-compose --profile production ps

echo "✅ Production environment is ready!"
echo "🌐 App available at: http://localhost"
echo "📊 API available at: http://localhost/api"

# ================================
# scripts/docker-stop.sh
#!/bin/bash
# Stop all Docker services

echo "🛑 Stopping Instagram Sentiment Analysis App..."
docker-compose down --remove-orphans

echo "🧹 Cleaning up unused images..."
docker image prune -f

echo "✅ All services stopped!"

# ================================
# scripts/docker-logs.sh
#!/bin/bash
# View logs from Docker services

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "📋 Available services:"
    echo "  flask_backend, celery_worker, redis, react_frontend, nginx"
    echo ""
    echo "Usage: $0 <service_name>"
    echo "Example: $0 flask_backend"
    echo ""
    echo "Or view all logs:"
    docker-compose logs --tail=50 -f
else
    echo "📋 Showing logs for: $SERVICE"
    docker-compose logs --tail=100 -f "$SERVICE"
fi

# ================================
# scripts/docker-shell.sh
#!/bin/bash
# Get shell access to running containers

SERVICE=${1:-flask_backend}

echo "🐚 Accessing shell for: $SERVICE"
docker-compose exec "$SERVICE" /bin/bash

# ================================
# requirements-dev.txt
# Development dependencies
-r requirements.txt

# Testing
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code quality
black==23.11.0
flake8==6.1.0
isort==5.12.0
mypy==1.7.1

# Development tools
flask-debugtoolbar==0.13.1
python-dotenv==1.0.0
watchdog==3.0.0

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==1.3.0

# Monitoring
flower==2.0.1
prometheus-flask-exporter==0.23.0

# ================================
# nginx/frontend.conf
# Nginx configuration for React frontend
server {
    listen 3000;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # Cache static assets
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}

# ================================
# nginx/nginx.conf
# Main Nginx configuration for production
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream backends
    upstream flask_backend {
        server flask_backend:8000;
        keepalive 32;
    }

    upstream react_frontend {
        server react_frontend:3000;
        keepalive 32;
    }

    # Main server block
    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self'" always;

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://flask_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Health checks
        location /health {
            proxy_pass http://flask_backend/health;
            access_log off;
        }

        # Frontend routes
        location / {
            proxy_pass http://react_frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files with caching
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
            proxy_pass http://react_frontend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}

# ================================
# .env.example
# Example environment variables file
# Copy this to .env and update with your values

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-in-production-make-it-long-and-random
HOST=0.0.0.0
PORT=8000

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
REACT_APP_API_URL=http://localhost:8000

# Instagram API (when you implement real API)
# INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
# INSTAGRAM_CLIENT_ID=your_instagram_client_id
# INSTAGRAM_CLIENT_SECRET=your_instagram_client_secret

# Celery Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=300

# Logging
LOG_LEVEL=INFO

# Monitoring (Flower)
FLOWER_BASIC_AUTH=admin:secure-password-here

# Production settings (uncomment for production)
# FLASK_ENV=production
# REACT_APP_ENV=production

# SSL Configuration (for production with HTTPS)
# SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
# SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Database (if you add one later)
# DATABASE_URL=postgresql://user:password@db:5432/sentiment_db

# External Services
# SENTRY_DSN=your-sentry-dsn-for-error-tracking
# REDIS_PASSWORD=your-redis-password-for-production

# ================================
# docker-compose.override.yml
# Override file for development (automatically loaded)
version: '3.8'

services:
  flask_backend:
    environment:
      - FLASK_ENV=development
    volumes:
      - .:/app  # Mount source code for development
    command: >
      bash -c "
        pip install -r requirements-dev.txt &&
        python app.py
      "

  celery_worker:
    volumes:
      - .:/app  # Mount source code for development
    command: >
      bash -c "
        pip install -r requirements-dev.txt &&
        celery -A tasks.instagram_sentiment_tasks worker --loglevel=debug --queues=instagram_queue,batch_queue --reload
      "

  react_frontend:
    command: npm start  # Use development server instead of production build