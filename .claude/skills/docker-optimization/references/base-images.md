# Base Image Selection Guide

## Image Type Comparison

| Type | Size | C Library | Attack Surface | Use Case |
|------|------|-----------|----------------|----------|
| Standard (Ubuntu/Debian) | 100MB+ | glibc | High | Development only |
| Alpine Linux | ~5-7MB | musl | Very Low | Simple Go/Rust static binaries |
| Debian/Ubuntu Slim | ~30-70MB | glibc | Moderate | **Production standard** for Python/Node/Java |
| Distroless | ~20-50MB | glibc/musl | Minimal | High-security production |
| Alpaquita Linux | ~10-20MB | Both | Low | Enterprise Java/Python with commercial support |
| Scratch | 0MB | N/A | None | Static binaries with no dependencies |

## Alpine Linux: When to Avoid

Alpine uses musl libc instead of glibc, causing:

1. **Threading Issues** - musl's memory allocator performs 6x worse under high concurrency
2. **DNS Resolution** - Different resolver behavior causes silent failures
3. **Native Extensions** - Node.js native modules, Python C extensions often fail
4. **Java Problems** - Thread stack size differences cause crashes

**Only use Alpine for:**
- Go with CGO_ENABLED=0
- Rust with static linking
- Simple services with no native dependencies

## Distroless Images

Google's distroless images contain only:
- The application runtime (JRE, Python interpreter)
- Application dependencies
- No shell, package manager, or system utilities

**Benefits:**
- Minimal attack surface
- Attacker cannot use curl, sh, apt for lateral movement
- Ideal for high-security environments

**Limitations:**
- No shell for debugging (use kubectl debug instead)
- Must copy all dependencies from builder stage

```dockerfile
FROM gcr.io/distroless/python3-debian12:latest
COPY --from=builder /app /app
CMD ["app/main.py"]
```

## Alpaquita Linux (BellSoft)

Enterprise-grade Alpine alternative offering:
- Both musl and glibc variants
- Commercial support with LTS
- Optimized musl without standard Alpine regressions
- Designed for Java/Python production workloads

## Scratch Image

The ultimate minimal image - completely empty filesystem.

**Requirements:**
- Fully statically linked binary
- No external dependencies
- No DNS resolution (unless embedded)

```dockerfile
FROM golang:1.22-alpine AS builder
RUN CGO_ENABLED=0 go build -o /app

FROM scratch
COPY --from=builder /app /app
ENTRYPOINT ["/app"]
```

## Image Pinning Strategy

### By Tag (Avoid in Production)
```dockerfile
FROM python:3.12
```
Risk: Tag can point to different images over time.

### By Version Tag
```dockerfile
FROM python:3.12.1-slim
```
Better but still mutable - security patches change content.

### By Digest (Recommended)
```dockerfile
FROM python:3.12.1-slim@sha256:abc123def456...
```
Guarantees exact same bits every build. Immutable.

**Finding the digest:**
```bash
docker pull python:3.12.1-slim
docker inspect python:3.12.1-slim --format='{{index .RepoDigests 0}}'
```
