import os

# Flask settings
SERVER_NAME = os.getenv('SERVER_NAME', '0.0.0.0')
SERVER_PORT = os.getenv('SERVER_PORT', 8081)
SERVICE_NAME = os.getenv('SERVICE_NAME', 'harpia-daemon')

FLASK_THREADED = os.getenv('FLASK_THREADED', True)
FLASK_DEBUG = os.getenv('FLASK_DEBUG', False)
URL_PREFIX = os.getenv('URL_PREFIX', '/api/v1')
SERVICE_NAMESPACE = os.getenv('SERVICE_NAMESPACE', 'dev')

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = os.getenv('RESTPLUS_SWAGGER_UI_DOC_EXPANSION', 'list')
RESTPLUS_VALIDATE = os.getenv('RESTPLUS_VALIDATE', True)
RESTPLUS_MASK_SWAGGER = os.getenv('RESTPLUS_MASK_SWAGGER', False)
RESTPLUS_ERROR_404_HELP = os.getenv('RESTPLUS_ERROR_404_HELP', False)

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOKI_SERVER = os.getenv('LOKI_SERVER', '')
LOKI_PORT = os.getenv('LOKI_PORT', 443)
LOKI_SCHEMA = os.getenv('LOKI_SCHEMA', 'https')

# SQLALCHEMY
DB_NAME = os.getenv('DB_NAME', 'harpia')
DB_USER = os.getenv('DB_USER', 'harpia')
DB_PASS = os.getenv('DB_PASS', 'harpia')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
SQLALCHEMY_DATABASE_URI = f'mariadb+mariadbconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8&use_unicode=0'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_ECHO = False
PROPAGATE_EXCEPTIONS = True
REQUESTS_CACHE_EXPIRE_SECONDS = 300

SMS_SERVICE = os.getenv('SMS_SERVICE', '')
VOICE_SERVICE = os.getenv('VOICE_SERVICE', '')
TEAMS_SERVICE = os.getenv('TEAMS_SERVICE', '')
TELEGRAM_SERVICE = os.getenv('TELEGRAM_SERVICE', '')
SLACK_SERVICE = os.getenv('SLACK_SERVICE', '')


class KafkaConfig:
    KAFKA_USER = os.getenv('KAFKA_USER', 'admin')
    KAFKA_PASS = os.getenv('KAFKA_PASS', 'admin')
    KAFKA_SERVERS = os.getenv('KAFKA_SERVERS', '127.0.0.1:9092')
    producer_message_send_max_retries = os.getenv('producer_message_send_max_retries', 6)
    producer_retry_backoff_ms = os.getenv('producer_retry_backoff_ms', 5000)
    producer_queue_buffering_max_ms = os.getenv('producer_queue_buffering_max_ms', 10000)
    producer_queue_buffering_max_messages = os.getenv('producer_queue_buffering_max_messages', 100000)
    producer_request_timeout_ms = os.getenv('producer_request_timeout_ms', 30000)
    consumer_session_timeout_ms = os.getenv('consumer_session_timeout_ms', 30000)
    consumer_heartbeat_interval_ms = os.getenv('consumer_heartbeat_interval_ms', 15000)


class DbConfig:
    USE_DB = os.getenv('USE_DB', False)
    DATABASE_SERVER = os.getenv('DATABASE_SERVER', '127.0.0.1')
    DATABASE_PORT = os.getenv('DATABASE_PORT', 3306)
    DATABASE_USER = os.getenv('DATABASE_USER', 'harpia')
    DATABASE_PSWD = os.getenv('DATABASE_PSWD', 'harpia')
    DATABASE_SCHEMA = os.getenv('DATABASE_SCHEMA', '')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DATABASE_USER}:{DATABASE_PSWD}@' \
                              f'{DATABASE_SERVER}:{DATABASE_PORT}/{DATABASE_SCHEMA}'
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    SQLALCHEMY_POOL_RECYCLE = os.getenv('', 300)


class TracingConfig:
    TEMPO_URL = os.getenv('TEMPO_URL', '')
