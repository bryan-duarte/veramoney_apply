# Langfuse Self-Hosted Auto-Initialization Report

> *"Why click buttons when environment variables can do the heavy lifting?"*
> — **El Barto**

## Executive Summary

Langfuse v3.x provides a **built-in automated provisioning system** that enables full initialization of organizations, users, projects, and API keys on container startup—zero UI interaction required. Your current configuration is 90% complete but missing two critical variables (`LANGFUSE_INIT_ORG_ID` and `LANGFUSE_INIT_PROJECT_ID`) that act as the initialization trigger.

---

## The Short Answer

**Yes, you can fully automate Langfuse initialization in Docker Compose.** No manual UI steps required.

---

## Complete Initialization Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `LANGFUSE_INIT_ORG_ID` | **YES** | Trigger: enables initialization system |
| `LANGFUSE_INIT_ORG_NAME` | No | Organization display name |
| `LANGFUSE_INIT_PROJECT_ID` | For API keys | Project unique identifier |
| `LANGFUSE_INIT_PROJECT_NAME` | No | Project display name |
| `LANGFUSE_INIT_PROJECT_PUBLIC_KEY` | For SDK | Pre-defined public API key |
| `LANGFUSE_INIT_PROJECT_SECRET_KEY` | For SDK | Pre-defined secret API key |
| `LANGFUSE_INIT_USER_EMAIL` | For user | Admin user email |
| `LANGFUSE_INIT_USER_NAME` | No | Admin user display name |
| `LANGFUSE_INIT_USER_PASSWORD` | For user | Admin password (min 8 chars) |

---

## How It Works

### Initialization Flow

```
Container Start
      │
      ▼
┌─────────────────────────┐
│ LANGFUSE_INIT_ORG_ID    │
│ is set?                 │
└───────────┬─────────────┘
            │
      YES   │   NO → Skip initialization
            ▼
┌─────────────────────────┐
│ 1. Create Organization  │
│    (upsert by ID)       │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 2. Create Project       │
│    (if PROJECT_ID set)  │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 3. Create API Keys      │
│    (if both keys set)   │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 4. Create Admin User    │
│    (if email+password)  │
└─────────────────────────┘
```

### Key Insight

The system uses **idempotent upsert operations**—safe to run on every container restart. If resources already exist, they're updated rather than duplicated.

---

## Your Current Configuration

### What You Have (`docker-compose.yml` lines 109-112)

```yaml
LANGFUSE_INIT_ORG_NAME: ${LANGFUSE_INIT_ORG_NAME:-VeraMoney}
LANGFUSE_INIT_PROJECT_NAME: ${LANGFUSE_INIT_PROJECT_NAME:-AI Platform}
LANGFUSE_INIT_PROJECT_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:-pk-default}
LANGFUSE_INIT_PROJECT_SECRET_KEY: ${LANGFUSE_SECRET_KEY:-sk-default}
```

### What's Missing

```yaml
LANGFUSE_INIT_ORG_ID: ${LANGFUSE_INIT_ORG_ID:-veramoney-org}      # REQUIRED TRIGGER
LANGFUSE_INIT_PROJECT_ID: ${LANGFUSE_INIT_PROJECT_ID:-veramoney-ai-platform}
```

**Without `LANGFUSE_INIT_ORG_ID`, the initialization system never activates.** All other variables are silently ignored.

---

## Complete Working Configuration

### docker-compose.yml (langfuse-web service)

```yaml
langfuse-web:
  image: docker.io/langfuse/langfuse:3
  environment:
    # ... existing variables ...

    # Initialization trigger (REQUIRED)
    LANGFUSE_INIT_ORG_ID: ${LANGFUSE_INIT_ORG_ID:-veramoney-org}
    LANGFUSE_INIT_ORG_NAME: ${LANGFUSE_INIT_ORG_NAME:-VeraMoney}

    # Project configuration
    LANGFUSE_INIT_PROJECT_ID: ${LANGFUSE_INIT_PROJECT_ID:-veramoney-ai-platform}
    LANGFUSE_INIT_PROJECT_NAME: ${LANGFUSE_INIT_PROJECT_NAME:-AI Platform}

    # API keys (both required for SDK integration)
    LANGFUSE_INIT_PROJECT_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:-pk-lf-0000000000000000}
    LANGFUSE_INIT_PROJECT_SECRET_KEY: ${LANGFUSE_SECRET_KEY:-sk-lf-000000000000000000000000}

    # Admin user (optional but recommended)
    LANGFUSE_INIT_USER_EMAIL: ${LANGFUSE_INIT_USER_EMAIL:-admin@veramoney.com}
    LANGFUSE_INIT_USER_NAME: ${LANGFUSE_INIT_USER_NAME:-Admin}
    LANGFUSE_INIT_USER_PASSWORD: ${LANGFUSE_INIT_USER_PASSWORD:-changeme123}
```

### .env File Additions

```bash
# Langfuse Auto-Initialization
LANGFUSE_INIT_ORG_ID=veramoney-org-001
LANGFUSE_INIT_ORG_NAME=VeraMoney
LANGFUSE_INIT_PROJECT_ID=veramoney-ai-platform
LANGFUSE_INIT_PROJECT_NAME=AI Platform
LANGFUSE_PUBLIC_KEY=pk-lf-your-32-char-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-64-char-secret-key-here
LANGFUSE_INIT_USER_EMAIL=admin@veramoney.com
LANGFUSE_INIT_USER_NAME=Administrator
LANGFUSE_INIT_USER_PASSWORD=SecurePassword123!
```

---

## API Key Format

| Key Type | Prefix | Length | Example |
|----------|--------|--------|---------|
| Public Key | `pk-lf-` | 32 chars | `pk-lf-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6` |
| Secret Key | `sk-lf-` | 64 chars | `sk-lf-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6` |

### Generate Secure Keys

```bash
# Public key (32 chars)
openssl rand -hex 16 | sed 's/^/pk-lf-/'

# Secret key (64 chars)
openssl rand -hex 32 | sed 's/^/sk-lf-/'
```

---

## Verification

After starting the stack:

```bash
# Check initialization logs
docker-compose logs langfuse-web | grep -i "init\|provision"

# Expected output:
# Running init scripts...
# Organization created/updated: veramoney-org
# Project created: veramoney-ai-platform
# API keys configured
# User created: admin@veramoney.com
```

### Verify in UI

1. Navigate to `http://localhost:3003`
2. Log in with `admin@veramoney.com` / `SecurePassword123!`
3. Organization "VeraMoney" exists with project "AI Platform"
4. API keys are available in Project Settings

---

## Technical Details

### Source Code References

| File | Purpose |
|------|---------|
| `web/src/env.mjs` | Environment variable schema validation |
| `web/src/initialize.ts` | Initialization logic implementation |
| `web/src/instrumentation.ts` | Initialization trigger on startup |

### Initialization Conditions

| Scenario | Behavior |
|----------|----------|
| `LANGFUSE_INIT_ORG_ID` not set | Initialization skipped entirely |
| Only org ID set | Organization created, no project |
| Org ID + Project ID set | Org + Project created, no API keys |
| All keys provided | Full setup: org, project, API keys |
| User email without password | Warning logged, user not created |
| Partial API keys (only one) | Warning logged, keys not created |

### User Role

Created users always receive **OWNER** role for the organization. There's no way to specify a different role through initialization variables.

---

## Limitations

| Limitation | Impact |
|------------|--------|
| Single user creation | Only one admin user can be auto-created |
| Fixed OWNER role | Cannot specify different user roles |
| No project membership | User gets org membership, must be added to projects manually |
| No team seeding | Cannot pre-configure additional team members |

---

## Sources

| Source | URL |
|--------|-----|
| Official docker-compose.yml | https://github.com/langfuse/langfuse/blob/main/docker-compose.yml |
| Environment schema | https://github.com/langfuse/langfuse/blob/main/web/src/env.mjs |
| Initialization logic | https://github.com/langfuse/langfuse/blob/main/web/src/initialize.ts |
| Production env example | https://github.com/langfuse/langfuse/blob/main/.env.prod.example |

---

## Key Findings

1. **Full automation is supported** - No UI interaction required for initial setup
2. **Your config is almost complete** - Just missing `ORG_ID` and `PROJECT_ID`
3. **Idempotent operations** - Safe to restart containers without duplication
4. **Pre-defined API keys** - Specify exact keys for immediate SDK integration
5. **Admin user auto-creation** - Optional but recommended for immediate access

---

## Recommendations

1. **Add the missing IDs** to your `docker-compose.yml`
2. **Generate secure API keys** using the openssl commands provided
3. **Set a strong admin password** in your `.env` file
4. **Test with fresh volumes** to verify initialization: `docker-compose down -v && docker-compose up -d`

---
*Report generated by: El Barto*
*Date: 2026-02-18*
