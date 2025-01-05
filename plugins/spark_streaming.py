from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from cassandra.cluster import Cluster
from datetime import datetime
import uuid

# Constants
KAFKA_TOPIC_NAME = "eventstream"
KAFKA_BOOTSTRAP_SERVER = "localhost:9092,localhost:9093,localhost:9094"
REDIS_HOST = "localhost"
REDIS_PORT = "6379"
CASSANDRA_HOST = "localhost"
KEYSPACE = "spark_streams"
TABLE = "created_users"
CHECKPOINT_LOCATION = "/tmp/check_point"
DATE_SAMPLE = "2024-07-17"

# Schema
event_schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("role_id", StringType(), True),
    StructField("game_id", StringType(), True),
    StructField("event_time", TimestampType(), True)
])

def create_spark_session():
    return SparkSession.builder \
        .appName("KafkaStructuredStreaming") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,"
                "com.redislabs:spark-redis_2.12:3.1.0,"
                "com.datastax.spark:spark-cassandra-connector_2.12:3.5.0") \
        .config("spark.redis.host", REDIS_HOST) \
        .config("spark.redis.port", REDIS_PORT) \
        .config("spark.redis.db", "0") \
        .config('spark.cassandra.connection.host', CASSANDRA_HOST) \
        .getOrCreate()

def read_kafka_stream(spark):
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER) \
        .option("subscribe", KAFKA_TOPIC_NAME) \
        .option("startingOffsets", "earliest") \
        .load()

def transform_event_df(kafka_stream):
    event_df = kafka_stream.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), event_schema).alias("data")) \
        .select("data.*")

    timestamp_format = "yyyy-MM-dd'T'HH:mm:ss.SSS"
    dateformats = "yyyy-MM-dd'T'HH:mm:00"
    start_window = "yyyy-MM-dd'T'00:00:ssXXX"
    end_window = "yyyy-MM-dd'T'23:59:59XXX"
    date = "yyyy-MM-dd"

    return event_df.withColumn("event_time", to_timestamp(col("event_time"), timestamp_format)) \
        .withColumn("event_time", date_format(col("event_time"), dateformats)) \
        .withColumn("time_start_window", date_format(col("event_time"), start_window)) \
        .withColumn("time_end_window", date_format(col("event_time"), end_window)) \
        .dropDuplicates() \
        .filter(date_format(col('event_time'), date) == DATE_SAMPLE)

def create_cassandra_connection():
    try:
        cluster = Cluster([CASSANDRA_HOST])
        return cluster.connect()
    except Exception as e:
        print(f"Could not create Cassandra connection due to {e}")
        return None

def create_keyspace(session):
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
    """)
    print('Keyspace created')

def create_table(session):
    session.execute(f"""
        CREATE TABLE IF NOT EXISTS {KEYSPACE}.{TABLE} (
            id UUID PRIMARY KEY,
            user_id TEXT,
            game_id TEXT,
            role_id TEXT,
            event_time TEXT
        )
    """)
    print("Table created successfully")

def generate_uuid():
    return str(uuid.uuid4())

def write_to_redis(batch_df, batch_id):
    batch_df.write \
        .format("org.apache.spark.sql.redis") \
        .option("table", "playing_time") \
        .option("key.column", "compose_id") \
        .mode("append") \
        .save()

def write_aggregate_to_redis(batch_df, batch_id):
    batch_df.write \
        .format("org.apache.spark.sql.redis") \
        .option("table", "total_playing_time") \
        .option("key.column", "user_id") \
        .mode("append") \
        .save()

def main():
    spark = create_spark_session()
    kafka_stream = read_kafka_stream(spark)
    event_df = transform_event_df(kafka_stream)

    uuid_udf = udf(generate_uuid, StringType())
    event_df = event_df.withColumn("id", uuid_udf())

    session = create_cassandra_connection()
    if session:
        create_keyspace(session)
        create_table(session)

    df_transformed = event_df
    transformed_df = df_transformed.groupBy("user_id", "game_id", "time_start_window", "time_end_window") \
        .agg(approx_count_distinct(struct("user_id", "game_id", "event_time")).alias("playing_time_minutes"))

    compose_key = transformed_df.withColumn("compose_id", concat(col("user_id"), lit(":"), col("game_id")))

    aggregates = df_transformed.groupBy("user_id", "time_start_window", "time_end_window") \
        .agg(approx_count_distinct(struct("user_id", "game_id", "event_time")).alias("playing_time_minutes"))

    query_compose_key = compose_key.writeStream \
        .outputMode("update") \
        .foreachBatch(write_to_redis) \
        .start()

    query_aggregate = aggregates.writeStream \
        .outputMode("update") \
        .foreachBatch(write_aggregate_to_redis) \
        .start()

    streaming_query = event_df.writeStream \
        .format("org.apache.spark.sql.cassandra") \
        .option('checkpointLocation', CHECKPOINT_LOCATION) \
        .option('keyspace', KEYSPACE) \
        .option('table', TABLE) \
        .start()

    query_compose_key.awaitTermination()
    query_aggregate.awaitTermination()
    streaming_query.awaitTermination()

if __name__ == "__main__":
    main()
