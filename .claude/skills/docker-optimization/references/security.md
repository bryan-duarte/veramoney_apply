# Container Security Hardening

## Non-Root User Configuration

Always run as non-root. Define user before CMD:

```dockerfile
FROM python:3.12-slim

RUN groupadd -r appgroup -g 1000 && \
    useradd -r -g appgroup -u 1000 appuser

WORKDIR /app
COPY --chown=appuser:appgroup . .

USER appuser
CMD ["python", "main.py"]
```

Fixed UID/GID ensures consistent permissions across environments.

## Capability Management

Drop all capabilities, add only what's needed:

```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE app
```

Common capabilities:
- `NET_BIND_SERVICE` - Bind to ports < 1024
- `CHOWN` - Change file ownership
- `SETUID/SETGID` - Set user/group ID

Most applications need none of these.

## Read-Only Filesystem

Prevent persistent malware installation:

```bash
docker run --read-only --tmpfs /tmp:rw,size=100m app
```

In docker-compose:
```yaml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp:rw,size=100m
      - /var/run:rw,size=10m
```

## Seccomp Profiles

Restrict syscalls with seccomp:

```bash
docker run --security-opt seccomp=profile.json app
```

Docker's default profile blocks ~44 dangerous syscalls. Customize for additional restrictions.

## AppArmor/SELinux

Apply mandatory access control:

```bash
docker run --security-opt apparmor=docker-default app
```

Custom profiles restrict:
- File access patterns
- Network operations
- Capability usage

## Secret Management

### Build-Time Secrets

Use BuildKit secret mounts - never ARG or ENV:

```dockerfile
RUN --mount=type=secret,id=api_key \
    export API_KEY=$(cat /run/secrets/api_key) && \
    ./configure
```

### Runtime Secrets

Use Docker secrets or external secret stores:

```yaml
services:
  app:
    secrets:
      - api_key
secrets:
  api_key:
    file: ./secrets/api_key.txt
```

Better: Use HashiCorp Vault, AWS Secrets Manager, or Kubernetes secrets.

## Vulnerability Scanning

### Pre-build scanning
```bash
trivy image --severity HIGH,CRITICAL myapp:latest
```

### Continuous scanning
```bash
docker scout cves myapp:latest
```

### In CI pipeline
```yaml
scan:
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL $IMAGE
```

## Supply Chain Security

### SBOM Generation

```bash
docker build --sbom=true -t myapp .
```

Syft alternative:
```bash
syft myapp:latest -o spdx > sbom.spdx.json
```

### Provenance Attestation

```bash
docker build --provenance=true -t myapp .
```

Creates SLSA provenance documenting:
- Build source repository
- Git commit
- Build parameters

### Image Signing

```bash
cosign sign --key cosign.key myregistry/myapp@sha256:digest
```

Verification:
```bash
cosign verify --key cosign.pub myregistry/myapp@sha256:digest
```

## Network Isolation

Disable inter-container communication:
```bash
docker run --icc=false app
```

Or in compose:
```yaml
services:
  app:
    networks:
      - frontend
networks:
  frontend:
    driver: bridge
    internal: true
```

## Resource Limits

Prevent resource exhaustion attacks:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```
