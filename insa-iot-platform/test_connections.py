#!/usr/bin/env python3
import asyncio
import asyncpg
import redis.asyncio as redis

async def test_connections():
    # Test PostgreSQL
    try:
        conn = await asyncpg.connect('postgresql://alkhorayef:AlkhorayefESP2025!@localhost:5440/esp_telemetry')
        await conn.close()
        print("✅ PostgreSQL connection OK")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

    # Test Redis
    try:
        r = await redis.from_url("redis://:RedisAlkhorayef2025!@localhost:6389", encoding="utf-8", decode_responses=True)
        await r.ping()
        await r.close()
        print("✅ Redis connection OK")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

    return True

if __name__ == "__main__":
    result = asyncio.run(test_connections())
    if result:
        print("\n✅ All services are accessible!")
    else:
        print("\n❌ Some services are not accessible")
