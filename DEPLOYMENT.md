# DocuSummarize - Deployment & Development Guide

## Development Setup

### 1. Local Development

```bash
# Clone repository
git clone <your-repo-url>
cd docusummarize

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Groq API key

# Run development server
python app.py
```

### 2. Docker Deployment

#### Prerequisites
- Docker
- Docker Compose
- Groq API Key

#### Steps

```bash
# 1. Build and start services
docker-compose up -d

# 2. Check logs
docker-compose logs -f api

# 3. Access API
# Swagger UI: http://localhost:8000/docs
# Health Check: http://localhost:8000/health

# 4. Stop services
docker-compose down
```

#### Environment Configuration
Create `.env` file:
```env
GROQ_API_KEY=your_api_key_here
QDRANT_API_KEY=admin
```

### 3. Testing Endpoints

#### Using cURL
```bash
# Health check
curl http://localhost:8000/health

# Upload and summarize PDF
curl -X POST "http://localhost:8000/summarize" \
  -H "accept: application/json" \
  -F "file=@document.pdf"

# Detailed summarization
curl -X POST "http://localhost:8000/summarize-detailed?include_chunks=true" \
  -H "accept: application/json" \
  -F "file=@document.pdf"
```

#### Using Python
```python
import requests

# File to summarize
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/summarize",
        files=files
    )
    print(response.json())
```

## Production Deployment

### Option 1: AWS EC2

```bash
# 1. SSH into EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# 2. Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# 3. Install Docker Compose
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone repository
git clone <your-repo>
cd docusummarize

# 5. Start services
docker-compose up -d
```

### Option 2: Heroku

```bash
# 1. Login to Heroku
heroku login

# 2. Create app
heroku create your-app-name

# 3. Set environment variables
heroku config:set GROQ_API_KEY=your_key

# 4. Deploy
git push heroku main
```

### Option 3: Railway

```bash
# 1. Connect GitHub repository to Railway
# 2. Set environment variables in Railway dashboard
# 3. Deploy automatically on push
```

## Performance Optimization

### 1. Caching
```python
# Add Redis caching for frequently summarized docs
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend

FastAPICache2.init(RedisBackend(url="redis://localhost"), prefix="docusummarize")
```

### 2. Load Balancing
```yaml
# Use nginx for load balancing across multiple instances
upstream api {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

### 3. Database Indexing
- Index Qdrant collections by document metadata
- Use pagination for large result sets

## Monitoring & Logging

### 1. Application Logging
```bash
# View logs
docker-compose logs -f api

# Export logs
docker-compose logs api > app.log
```

### 2. Health Monitoring
```bash
# Add monitoring endpoint
curl http://localhost:8000/metrics
```

### 3. Error Tracking
```python
# Integrate with Sentry
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)
```

## Troubleshooting

### Issue: Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Issue: Vector Store Connection Failed
```bash
# Ensure Qdrant is running
docker-compose ps

# Restart Qdrant
docker-compose restart qdrant
```

### Issue: Out of Memory
```bash
# Increase container memory
docker-compose down
# Edit docker-compose.yml, add:
# services:
#   api:
#     mem_limit: 2g

docker-compose up -d
```

## CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t docusummarize .
      
      - name: Run tests
        run: docker run docusummarize pytest
      
      - name: Push to registry
        run: |
          docker tag docusummarize your-registry/docusummarize
          docker push your-registry/docusummarize
      
      - name: Deploy to production
        run: |
          # Deploy commands here
```

## API Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/summarize")
@limiter.limit("10/minute")
async def summarize_pdf(request: Request, file: UploadFile):
    ...
```

## Security Best Practices

1. ✅ Always use HTTPS in production
2. ✅ Validate and sanitize file uploads
3. ✅ Store API keys in environment variables
4. ✅ Implement rate limiting
5. ✅ Use authentication tokens for API access
6. ✅ Regular security audits
7. ✅ Keep dependencies updated

## Scaling Strategies

1. **Horizontal Scaling**: Add more API instances behind load balancer
2. **Vertical Scaling**: Increase server resources
3. **Caching**: Implement Redis for result caching
4. **Queue Processing**: Use Celery for async tasks
5. **CDN**: Use CDN for static assets

---

For more information, see [README.md](README.md)
