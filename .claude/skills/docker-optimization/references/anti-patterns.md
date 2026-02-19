# Docker Anti-Patterns

## UPX Compression

**What it is:** Compressing binaries with UPX to reduce size.

**Why avoid it:**

1. **Memory bloat** - Compressed binaries decompress entirely into RAM at startup. A 10MB compressed binary can use 30MB+ RSS.

2. **Security false positives** - Malware uses similar packing techniques. UPX binaries frequently flagged by security scanners.

3. **Debugging difficulty** - Profilers and debuggers (gdb, perf) cannot analyze packed binaries.

4. **Startup latency** - Decompression adds CPU overhead before application runs.

**Verdict:** Never use for production containers. Size savings don't justify the trade-offs.

## Layer Squashing (--squash)

**What it is:** Merging all layers into single layer.

**Why avoid it:**

1. **No layer sharing** - If 10 images share Debian slim base, Docker downloads it once. With squashing, each image is unique.

2. **Increased bandwidth** - Every pull downloads entire image history.

3. **Registry bloat** - No deduplication of common layers.

4. **Lost metadata** - Build history and layer provenance disappear.

**Better alternative:** Use multi-stage builds to achieve same size benefits while preserving layer efficiency.

## :latest Tag in Production

**What it is:** Using floating tag `:latest` or major version only `:3.12`.

**Why avoid it:**

1. **Unreproducible builds** - Same Dockerfile produces different images over time.

2. **Silent failures** - Security patches can change behavior unexpectedly.

3. **No rollback** - Cannot recreate exact production image.

**Correct approach:**
```dockerfile
FROM python:3.12.1-slim@sha256:abc123...
```

## apt-get upgrade

**What it is:** Running `apt-get upgrade` during build.

**Why avoid it:**

1. **Unreproducible** - Package versions change between builds.

2. **Slow builds** - Full system upgrade every build.

3. **Large layers** - Upgrades create additional layer overhead.

**Correct approach:**
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        package=1.2.3 && \
    rm -rf /var/lib/apt/lists/*
```

## Installing Build Tools in Final Image

**What it is:** Including gcc, make, node with devDependencies in production.

**Why avoid it:**

1. **Large attack surface** - Compilers enable code generation attacks.

2. **Bloat** - Hundreds of MB of unnecessary tools.

3. **Compliance risk** - Security scanners flag development packages.

**Correct approach:** Multi-stage builds with dedicated builder stage.

## COPY . . at Start

**What it is:** Copying entire context before dependency installation.

**Why avoid it:**

1. **Cache invalidation** - Any file change invalidates all subsequent layers.

2. **Slow rebuilds** - Dependencies reinstalled on every code change.

**Correct approach:**
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

## Running as Root

**What it is:** Default behavior when no USER specified.

**Why avoid it:**

1. **Container escape** - Root in container can exploit kernel vulnerabilities.

2. **Host compromise** - Mounted volumes editable by attacker.

3. **Compliance violation** - Security policies reject root containers.

4. **Privilege escalation** - Attacker can install packages, create users.

## Ignoring .dockerignore

**What it is:** No .dockerignore file or incomplete patterns.

**Why avoid it:**

1. **Large build context** - Sending gigabytes to daemon.

2. **Slow builds** - Context transfer dominates build time.

3. **Security risk** - Copying .env, secrets, credentials.

**Correct .dockerignore:**
```
.git
.gitignore
.env
.env.*
node_modules
__pycache__
*.pyc
.venv
venv
.pytest_cache
.coverage
htmlcov
*.md
Dockerfile*
docker-compose*
```

## Single-Stage Builds for Complex Apps

**What it is:** One FROM statement for entire build.

**Why avoid it:**

1. **Large images** - Build tools and dependencies included.

2. **Security surface** - Compilers, debuggers available to attackers.

3. **Slow deploys** - Large images take longer to pull.

## Excessive RUN Instructions

**What it is:** Many separate RUN commands.

**Why avoid it:**

1. **Layer proliferation** - Each RUN creates a layer.

2. **Metadata overhead** - Layer headers add to image size.

**Correct approach:** Chain commands with `&&`:
```dockerfile
RUN apt-get update && \
    apt-get install -y package && \
    rm -rf /var/lib/apt/lists/*
```
