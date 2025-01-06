from fastapi import FastAPI
import redis
import json
from typing import Optional
app = FastAPI()

# Redis Connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

@app.get("/user_playing_time")
async def get_specific_playing_time(user_id: str, game_id: Optional[str] = None):
    print(game_id)
    print(user_id)
    if game_id == None:
        hash_key = f"total_playing_time:{user_id}"
        hash_data = redis_client.hgetall(hash_key)
        if hash_data:
            data = {
            "user_id": user_id,
            "playing_time_minutes": hash_data['playing_time_minutes'],
            "time_window": hash_data['time_start_window'] +' '+ 'to' +' '+ hash_data['time_end_window']
            }
            return data
    else:
        hash_key = f"playing_time:{user_id}:{game_id}"
        print(hash_key)
        hash_data = redis_client.hgetall(hash_key)

        if hash_data:
            data = {
            "user_id": user_id,
            "game_id": game_id,
            "playing_time_minutes": hash_data['playing_time_minutes'],
            "time_window": hash_data['time_start_window'] +' '+ 'to' +' '+ hash_data['time_end_window']
            }
            return data
    
