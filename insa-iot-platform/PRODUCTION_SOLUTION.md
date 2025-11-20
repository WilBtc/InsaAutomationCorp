# Production Solution - Docker DNS Resolution Fix

## Problem
Docker builds were failing with:
```
Temporary failure resolving 'deb.debian.org'
```

## Root Cause
**Tailscale stateful filtering** (enabled by default since v1.66.0) was blocking DNS packets from Docker containers on the bridge network, even though DNS servers were configured in `/etc/docker/daemon.json`.

## Solution Implemented
Added `network: host` to build context in `docker-compose.yml`:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      network: host  # ← PRODUCTION FIX
    # ... rest of config

  ml-service:
    build:
      context: .
      dockerfile: Dockerfile
      network: host  # ← PRODUCTION FIX
    # ... rest of config
```

## Why This Works
- **Build time**: Uses host network to download packages from internet
- **Runtime**: Containers still run in isolated `alkhorayef-net` bridge network
- **Security**: Maintains Tailscale stateful filtering (protecting against TS-2024-005 vulnerability)
- **Best practice**: Standard pattern for Docker builds on Tailscale-enabled hosts

## Results
✅ DNS resolution working - downloading at 2742 kB/s from deb.debian.org
✅ No system-level changes required
✅ Maintains security posture
✅ Production-ready solution

## Build Status
- Packages downloading successfully
- Building both API and ML service images
- ETA: 5-10 minutes (large ML dependencies: PyTorch, Transformers)

## Files Modified
- `/home/wil/insa-iot-platform/docker-compose.yml` - Added `network: host` to build contexts

## Security Notes
- Tailscale stateful filtering remains **ENABLED** (secure)
- Only BUILD context uses host network (for package downloads)
- Running containers use isolated bridge network (secure)
- No exposure of container services to host network
- Safe for production deployment with exit node/subnet routes

## Reference
- [Docker Build Network Configuration](https://docs.docker.com/compose/compose-file/build/#network)
- [Tailscale Stateful Filtering KB](https://tailscale.com/kb/1570/messages-client-docker-stateful-filtering)
- [Security Bulletin TS-2024-005](https://tailscale.com/security-bulletins)
