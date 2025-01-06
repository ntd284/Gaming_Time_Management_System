import redis
def time_to_flush():
    try:
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        redis_client.flushdb()
        print("✅ Redis flushed successfully!")
    except:
        print("❌ Redis flush failed!")
time_to_flush()