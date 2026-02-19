# BuildKit Patterns

## BuildKit vs Legacy Builder

| Feature | Legacy | BuildKit |
|---------|--------|----------|
| Execution | Sequential | Parallel graph |
| Cache | String matching | Content-addressed |
| Unused stages | Always built | Skipped automatically |
| Cache export | Not supported | Registry/local export |
| Mount types | None | cache, secret, ssh, bind |

## Cache Mounts by Language

### Python (pip)
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Python (uv)
```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements.txt
```

### Node.js (npm)
```dockerfile
RUN --mount=type=cache,target=/root/.npm \
    npm ci
```

### Node.js (yarn)
```dockerfile
RUN --mount=type=cache,target=/root/.yarn \
    yarn install --frozen-lockfile
```

### Rust (cargo)
```dockerfile
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release
```

### Go (modules)
```dockerfile
RUN --mount=type=cache,target=/go/pkg/mod \
    go build -o /app
```

### Debian/Ubuntu (apt)
```dockerfile
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y package
```

## Secret Mounts

Never embed credentials in image layers. Use secret mounts:

```dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

Build command:
```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

## SSH Mounts

For private repositories:

```dockerfile
RUN --mount=type=ssh \
    git clone git@github.com:org/private-repo.git
```

Build command:
```bash
docker build --ssh default .
```

## Parallel Stage Execution

BuildKit executes independent stages concurrently:

```dockerfile
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /backend
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
RUN python -m compileall .

FROM nginx:alpine AS runtime
COPY --from=frontend /frontend/dist /usr/share/nginx/html
COPY --from=backend /backend /app
```

Frontend and backend stages run in parallel.

## Cache Export/Import

Export cache to registry for CI/CD:

```bash
docker build \
  --cache-from type=registry,ref=myregistry/myapp:cache \
  --cache-to type=registry,ref=myregistry/myapp:cache,mode=max \
  -t myregistry/myapp:latest .
```

Or to local directory:

```bash
docker build \
  --cache-from type=local,src=/tmp/docker-cache \
  --cache-to type=local,dest=/tmp/docker-cache,mode=max \
  -t myapp:latest .
```

## Multi-Stage Reuse

Share base stages across images:

```dockerfile
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y common-deps
WORKDIR /app

FROM base AS builder
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS runtime
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . .
CMD ["python", "main.py"]
```

## Inline Cache

Enable inline cache for simpler CI:

```bash
docker build \
  --cache-from myapp:latest \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t myapp:latest .
```
