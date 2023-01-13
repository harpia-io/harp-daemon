from logger.logging import service_logger
from harp_daemon.settings import KafkaConfig, SERVICE_NAME
from confluent_kafka import Consumer
import ujson as json
from harp_daemon.worker import ProcessNotification
from harp_daemon.handlers.auto_resolve import AutoResolve
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor

log = service_logger()


class ProcessMessage(object):
    def __init__(self, kafka_topic):
        self.kafka_topic = kafka_topic

    def start_consumer(self):
        """
        Start consumer
        """
        log.info(msg=f"Starting consumer - ProcessMessage")
        instrumentation = ConfluentKafkaInstrumentor()

        consumer = Consumer(
            {
                'bootstrap.servers': KafkaConfig.KAFKA_SERVERS,
                'group.id': SERVICE_NAME,
                'auto.offset.reset': 'latest',
            }
        )
        consumer = instrumentation.instrument_consumer(consumer)

        consumer.subscribe([self.kafka_topic])

        log.info(msg=f"Consumer!!! - ProcessMessage has been started")

        while True:
            msg = consumer.poll(5.0)
            if msg is None:
                continue
            if msg.error():
                log.error(msg=f"Failed to consume message from Kafka: {msg.error()}")
                continue

            parsed_json = json.loads(msg.value().decode('utf-8'))

            log.info(
                msg=f"Consumed message from Kafka\nparsed_json: {parsed_json}"
            )

            ProcessNotification(notification=parsed_json).main()

        return consumer


class AutoResolveMessage(object):
    def __init__(self, kafka_topic):
        self.kafka_topic = kafka_topic

    def start_consumer(self):
        """
        Start consumer
        """

        log.debug(msg=f"Starting consumer - AutoResolveMessage")

        instrumentation = ConfluentKafkaInstrumentor()

        consumer = Consumer(
            {
                'bootstrap.servers': KafkaConfig.KAFKA_SERVERS,
                'group.id': SERVICE_NAME,
                'auto.offset.reset': 'latest',
            }
        )
        consumer = instrumentation.instrument_consumer(consumer)

        consumer.subscribe([self.kafka_topic])

        log.debug(msg=f"Consumer - AutoResolveMessage has been started")

        while True:
            msg = consumer.poll(5.0)

            if msg is None:
                continue
            if msg.error():
                log.error(msg=f"Failed to consume message from Kafka: {msg.error()}")
                continue

            parsed_json = json.loads(msg.value().decode('utf-8'))

            log.info(
                msg=f"Consumed message from Kafka\nparsed_json: {parsed_json}",
                extra={"tags": {}}
            )

            AutoResolve(alert_ids=parsed_json['alert_ids'], event_id=parsed_json['event_id']).process_resolve()

        return consumer


class KafkaConsumeMessages(object):
    def __init__(self, kafka_topic):
        self.kafka_topic = kafka_topic

    def start_consumer(self):
        """
        Start consumer
        """

        log.debug(f"Initializing Kafka Confluent Consumer - {SERVICE_NAME}. Topic - {self.kafka_topic}")

        consumer = Consumer(
            {
                'bootstrap.servers': KafkaConfig.KAFKA_SERVERS,
                'group.id': SERVICE_NAME,
                'auto.offset.reset': 'latest',
                'allow.auto.create.topics': True,
                'session.timeout.ms': KafkaConfig.consumer_session_timeout_ms,
                'heartbeat.interval.ms': KafkaConfig.consumer_heartbeat_interval_ms,
                'offset.store.method': 'broker'
            }
        )

        consumer.subscribe([self.kafka_topic])

        return consumer
