import time
from kafka import KafkaProducer
import json
file_path = "/Users/macos/Documents/Python/Project-CV/VNG/VNG-Assignment/files"
KAFKA_TOPIC_NAME = 'eventstream'
def generate_data():
    producer = KafkaProducer(
    bootstrap_servers = "localhost:9092,localhost:9093,localhost:9094",
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
    )
    with open(file_path + '/sample_file.json') as f:
        events = json.load(f)
        # while(True):
        for message in events:
            print("KAFKA_TOPIC_NAME",KAFKA_TOPIC_NAME,message)
            producer.send(KAFKA_TOPIC_NAME,message)
            producer.flush()
            # time.sleep(1)


if __name__ == '__main__':
    generate_data()