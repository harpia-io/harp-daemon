from logger.logging import service_logger
from harp_daemon.settings import KafkaConfig
import traceback
from prometheus_client import Summary
from confluent_kafka import Producer
import json
import datetime
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
from harp_daemon.plugins.tracer import get_tracer

logger = service_logger()
tracer = get_tracer().get_tracer(__name__)
instrumentation = ConfluentKafkaInstrumentor()


class KafkaProduceMessages(object):
    KAFKA_PRODUCER_START = Summary('kafka_confluent_producer_start_latency_seconds', 'Time spent starting Kafka producer')
    KAFKA_PRODUCE_MESSAGES = Summary('kafka_confluent_produce_messages_latency_seconds', 'Time spent processing produce to Kafka')

    def __init__(self):
        self.producer = self.init_producer()

    @staticmethod
    @KAFKA_PRODUCER_START.time()
    def init_producer():
        try:
            producer_config = {
                'bootstrap.servers': KafkaConfig.KAFKA_SERVERS
            }

            producer = Producer(**producer_config)

            return instrumentation.instrument_producer(producer)
        except Exception as err:
            logger.error(
                msg=f"Can`t connect to Kafka cluster - {KafkaConfig.KAFKA_SERVERS}\nError: {err}\nTrace: {traceback.format_exc()}"
            )
            return None

    @staticmethod
    def default_converter(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    @staticmethod
    def delivery_report(err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            logger.error('Message delivery failed: {}'.format(err))
        else:
            logger.debug('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    @KAFKA_PRODUCE_MESSAGES.time()
    @tracer.start_as_current_span("Kafka: produce_message")
    def produce_message(self, topic, message):
        logger.debug(
            msg=f"Start producing message to topic - {topic}\nBody: {message}"
        )
        try:
            self.producer.produce(
                topic,
                json.dumps(message, default=self.default_converter).encode(),
                callback=self.delivery_report
            )

            self.producer.flush()
        except Exception as err:
            logger.error(
                msg=f"Can`t push message to - {topic}\nBody: {message}\nError: {err}\nTrace: {traceback.format_exc()}"
            )
