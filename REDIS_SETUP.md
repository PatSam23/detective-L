# Week 3: Redis Caching Setup Guide

## Architecture

```
Request → Check Redis Cache (SHA256 hash of provider+model+messages)
         → Cache HIT: Return cached response (instant)
         → Cache MISS: Call LLM Provider → Store in Redis (24h TTL) → Return response
```

## Cache Key Generation

- **Format**: `cache:provider:model:hash`
- **Hash**: SHA256(provider + model + normalized_messages_json)
- **TTL**: 24 hours (configurable via `CACHE_TTL` env var)

## Setup Options

### Option 1: Redis via WSL + Docker (Recommended)

Requires Windows Subsystem for Linux (WSL) and Docker Desktop.

```powershell
# Start Redis container
docker-compose up -d redis

# Verify it's running
docker-compose ps

# View logs
docker-compose logs redis

# Stop Redis
docker-compose down
```

### Option 2: Redis Natively on Windows

Install [Redis for Windows](https://github.com/microsoftarchive/redis/releases):

```powershell
# Download MSI installer and run
# Or use Chocolatey
choco install redis-64

# Start Redis server
redis-server

# In another terminal, test connection
redis-cli ping
# Expected output: PONG
```

### Option 3: Redis Cloud (Development)

Use [Redis Cloud Free Tier](https://redis.com/cloud/):

1. Create account and free database
2. Copy connection string
3. Update `.env`:
   ```
   REDIS_HOST=your-cloud-host.redis.cloud.com
   REDIS_PORT=6379
   REDIS_PASSWORD=your-password
   ```

## Environment Variables

Located in `backend/.env`:

```env
# Redis Connection
REDIS_HOST=localhost          # Redis server hostname
REDIS_PORT=6379              # Redis port
REDIS_DB=0                    # Redis database number
REDIS_PASSWORD=               # Optional: password (leave empty for local)

# Cache Settings
CACHE_TTL=86400              # Cache TTL in seconds (24 hours)
CACHE_ENABLED=true           # Enable/disable caching globally
```

## Testing

### 1. Unit Tests (No Redis Required)

Run cache unit tests:

```bash
cd backend
python test_cache.py
```

Output shows:
- ✓ Cache HIT/MISS logic
- ✓ Different queries → different cache keys
- ✓ Provider isolation
- ✓ Statistics tracking
- ✓ Cache clear operations

### 2. End-to-End Test (Requires Redis Running)

Start the backend server:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

In another terminal, test gateway with caching:

```bash
# First request (cache MISS)
curl -X POST http://localhost:8000/gateway/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'

# Second request (cache HIT - instant)
curl -X POST http://localhost:8000/gateway/chat \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'

# Check cache stats
curl http://localhost:8000/cache/stats
```

Expected output on second request (cache HIT):
```json
{
  "cache": {
    "hits": 1,
    "misses": 1,
    "errors": 0,
    "total": 2,
    "hit_rate_percent": 50.0,
    "connected": true,
    "enabled": true
  },
  "message": "Cache statistics (track LLM call reduction)"
}
```

### 3. Full Research Pipeline

Test caching with the full research workflow:

```bash
# Frontend at port 3000
cd frontend
npm run dev

# Backend at port 8000
cd backend
uvicorn main:app --reload

# Run research query twice
# First: Full agent pipeline execution (no cache)
# Second: All LLM calls should hit cache → faster response
```

Watch server logs for:
```
📦 Cache HIT: gemini/gemini-2.5-flash (stats: {'hits': 1, 'misses': 0, ...})
💾 Cache MISS → Stored: gemini/gemini-2.5-flash (stats: {'hits': 1, 'misses': 1, ...})
```

## Monitoring

### Real-time Logs

Backend logs show cache activity:

```
✓ Connected to Redis at localhost:6379
✓ Cache HIT: cache:gemini:gemini-2.5-flash:abc123
💾 Cache MISS → Stored: cache:gemini:gemini-2.5-flash:def456 (TTL: 86400s)
📊 Cache stats: hits=5, misses=2, hit_rate=71.43%
```

### API Endpoint

Check live cache stats anytime:

```bash
curl http://localhost:8000/cache/stats | jq
```

## Cost Impact Estimation

| Scenario | Without Cache | With Cache | Savings |
|----------|---------------|-----------|---------|
| 10 identical queries | 10 API calls | 1 API call | 90% ↓ |
| 100 queries (50% duplicates) | 100 API calls | 50 API calls | 50% ↓ |
| Daily research (200 queries) | ~$5/day | ~$2.50/day | 50% ↓ |

*Estimates based on ~$0.025 per 1K input tokens (Gemini pricing)*

## Troubleshooting

### "Connection refused" on localhost:6379

**Issue**: Redis not running

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# If not, start it
redis-server

# Or with Docker
docker-compose up -d redis
```

### Cache not working (always MISS)

**Check**:
1. Is Redis enabled? `CACHE_ENABLED=true` in `.env`
2. Is Redis connected? Check server logs: `✓ Connected to Redis...`
3. Are you sending identical messages? Cache key = SHA256(provider+model+messages)

**Debug**:
```bash
# View Redis keys
redis-cli
> KEYS cache:*
> TTL cache:gemini:gemini-2.5-flash:abc123
```

### High error rate

**Solution**:
- Check Redis disk space
- Check Redis memory limit: `CONFIG GET maxmemory`
- Monitor with: `INFO stats`

## Next Steps

- Week 4: Add PostgreSQL for request tracking
- Week 5: Add rate limiting & failover
- Week 6: Add Prometheus metrics & deployment
