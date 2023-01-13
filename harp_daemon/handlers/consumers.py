# from logger.logging import service_logger
# import ujson as json
# import traceback
# from harp_daemon.handlers.auto_resolve import AutoResolve
# from microservice_template_core.tools.kafka_confluent_consumer import KafkaConsumeMessages
#
#
# logger = service_logger()
#
#
# class ConsumeMessages(object):
#     def __init__(self, topic):
#         self.topic = topic
#
#     @staticmethod
#     def process_message(parsed_json):
#         processor = AutoResolve(alert_ids=parsed_json['alert_ids'], event_id=parsed_json['event_id'])
#         processor.process_resolve()
#
#     def start_consumer(self):
#         """
#         Start metrics consumer
#         """
#
#         consumer = KafkaConsumeMessages(kafka_topic=self.topic).start_consumer()
#
#         while True:
#             msg = consumer.poll(5.0)
#
#             if msg is None:
#                 continue
#             if msg.error():
#                 logger.error(msg=f"Consumer error: {msg.error()}")
#                 continue
#
#             parsed_json = None
#             try:
#                 parsed_json = json.loads(msg.value().decode('utf-8'))
#
#                 logger.debug(
#                     msg=f"Consumer event from Kafka\n{parsed_json}",
#                     extra={"tags": {}}
#                 )
#
#                 self.process_message(parsed_json)
#             except ConnectionResetError as err:
#                 logger.warning(msg=f"Can`t connect to DB: {err}\nStack: {traceback.format_exc()}\n{parsed_json}")
#                 continue
#             except Exception as err:
#                 logger.error(msg=f"Exception in Thread: {err}\nStack: {traceback.format_exc()}\n{parsed_json}")
#                 exit()
#
#     def main(self):
#         try:
#             self.start_consumer()
#         except Exception as err:
#             logger.error(msg=f"Exception during processing message from Kafka: {err}")
#
#
