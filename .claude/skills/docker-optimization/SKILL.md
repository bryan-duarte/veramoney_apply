---
name: docker-optimization
description: Docker image optimization for production workloads focusing on size reduction, build performance, security hardening, and reproducibility. Use when optimizing Dockerfiles, reducing image sizes, improving build times, configuring multi-stage builds, setting up BuildKit cache mounts, selecting base images, hardening container security, implementing SBOM/attestations, or fixing Docker anti-patterns. Triggers include "optimize this Dockerfile", "reduce image size", "make builds faster", "secure container", "multi-stage build", "which base image", "docker best practices".
---

# Docker Image Optimization

## Workflow

1. **Analyze current Dockerfile** - Identify inefficiencies, large layers, missing cache usage
2. **Select base image** - Match image type to workload requirements
3. **Implement multi-stage build** - Separate build from runtime
4. **Add BuildKit cache mounts** - Persist dependency downloads
5. **Apply security hardening** - Non-root user, read-only filesystem
6. **Enable reproducibility** - Pin by digest, use lockfiles
7. **Add supply chain metadata** - SBOM and provenance attestations

## Base Image Selection

| Language/Runtime | Recommended Image | Reason |
|------------------|-------------------|--------|
| Python | `python:3.12-slim` | glibc stability, small size |
| Node.js | `node:22-bookworm-slim` | glibc compatibility |
| Go | `golang:1.22-alpine` (build) → `scratch` or `distroless` | Static binary |
| Rust | `rust:1.78-alpine` (build) → `distroless` | Minimal runtime |
| Java | `eclipse-temurin:21-jre` | Production-ready JRE |

**Avoid Alpine for Python/Node.js/Java** - musl libc causes threading issues, DNS resolution problems, and native extension failures.

For detailed base image comparison, see [references/base-images.md](references/base-images.md).

## Multi-Stage Build Pattern

```
# Stage 1: Build
FROM language:version-slim AS builder
WORKDIR /build
COPY package-files ./
RUN --mount=type=cache,target=/cache/dir \
    install-dependencies
COPY source ./
RUN build-command

# Stage 2: Runtime
FROM language:version-slim AS runtime
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /build/artifacts ./
USER appuser
CMD ["start-command"]
```

## BuildKit Cache Mounts

Cache mounts persist dependency downloads between builds without bloating the image.

| Tool | Cache Target |
|------|--------------|
| pip | `/root/.cache/pip` |
| npm | `/root/.npm` |
| yarn | `/root/.yarn` |
| cargo | `/usr/local/cargo/registry` |
| go mod | `/go/pkg/mod` |
| apt | `/var/cache/apt` |

Example:
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

For advanced BuildKit patterns, see [references/buildkit-patterns.md](references/buildkit-patterns.md).

## Security Hardening Checklist

- [ ] Define non-root USER before CMD
- [ ] Create dedicated user/group with fixed UID/GID
- [ ] Set `--chown` on COPY commands
- [ ] Use `--cap-drop=ALL` and add only required capabilities
- [ ] Consider `--read-only` filesystem with tmpfs for /tmp
- [ ] Never store secrets in image layers (use `--mount=type=secret`)

For complete security guidance, see [references/security.md](references/security.md).

## Reproducibility

**Pin base images by digest:**
```dockerfile
FROM python:3.12.1-slim@sha256:abc123...
```

**Enable deterministic timestamps:**
```bash
export SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)
docker build --build-arg SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH .
```

## Supply Chain Metadata

```bash
docker build \
  --sbom=true \
  --provenance=true \
  --tag myimage:latest .
```

Sign with Cosign:
```bash
cosign sign myregistry/myimage@sha256:digest
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| `:latest` tag | Unpredictable builds | Pin to digest |
| UPX compression | 3x RSS, security false positives | Skip compression |
| `--squash` | Breaks layer sharing | Use multi-stage |
| Root user | Container escape risk | Non-root USER |
| `apt-get upgrade` | Unreproducible | Pin package versions |
| Single monolithic stage | Large images | Multi-stage build |

For detailed anti-pattern analysis, see [references/anti-patterns.md](references/anti-patterns.md).

## Templates

Ready-to-use Dockerfile templates in `assets/`:
- `Dockerfile.python` - Python multi-stage with uv
- `Dockerfile.nodejs` - Node.js with npm cache mount
- `Dockerfile.go` - Go static binary to scratch

## Quick Reference Commands

```bash
# Build with BuildKit
DOCKER_BUILDKIT=1 docker build -t app .

# Analyze image layers
docker history app:latest --no-trunc
dive app:latest

# Security scan
docker scout cves app:latest
trivy image app:latest

# Export build cache
docker build --cache-to type=registry,ref=mycache --cache-from type=registry,ref=mycache .
```
