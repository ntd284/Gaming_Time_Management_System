import time
from kafka import KafkaProducer
import json
import requests

def get_data_from_http():
    response = requests.get("https://github.com/ntd284/VNG-Assignment/raw/refs/heads/main/files/sample_file.json")
    response = response.json()
    return response

def generate_data():
    response = get_data_from_http()
    producer = KafkaProducer(
    bootstrap_servers = "localhost:9092,localhost:9093,localhost:9094",
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
    )
    for message in response:
        print("KAFKA_TOPIC_NAME",KAFKA_TOPIC_NAME,message)
        producer.send(KAFKA_TOPIC_NAME,message)
        producer.flush()

if __name__ == '__main__':
    KAFKA_TOPIC_NAME = 'eventstream'
    generate_data()