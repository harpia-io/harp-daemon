import os

BOTS_SERVICE = os.getenv('BOTS_SERVICE', 'https://127.0.0.1/harp-bots/api/v1/bots')
DAEMON_THREADS = int(os.getenv('DAEMON_THREADS', 1))
COLLETOR_NOTIFICATIONS_TOPIC = os.getenv('COLLETOR_NOTIFICATIONS_TOPIC', 'harpia-notifications')
KAFKA_SERVERS = os.getenv('KAFKA_SERVERS', '127.0.0.1:9092')
LICENSE_SERVICE = os.getenv('LICENSE_SERVICE', 'https://127.0.0.1/harp-licenses/api/v1/licenses/verify')
ENVIRONMENTS_HOST = os.getenv("ENVIRONMENTS_HOST", "https://127.0.0.1/harp-environments/api/v1/environments")
SCENARIOS_HOST = os.getenv('SCENARIOS_HOST', 'https://127.0.0.1/harp-scenarios/api/v1/scenarios')

KAFKA_CONSUMER_THREADS = int(os.getenv('KAFKA_CONSUMER_THREADS', 1))
RESOLVE_NOTIFICATIONS_TOPIC = os.getenv('RESOLVE_NOTIFICATIONS_TOPIC', 'harpia-resolve-notifications')
ENV_DELETION_TOPIC = os.getenv('ENV_DELETION_TOPIC', 'harpia-environment-update')

# EMAIL Bot:
SMTP_ACTIVE = os.getenv('SMTP_ACTIVE', True)
SMTP_HOST = os.getenv('SMTP_HOST', 'smtpout.secureserver.net')
SMTP_PORT = int(os.getenv('SMTP_PORT', 465))

# JIRA Bot:
JIRA_ACTIVE = os.getenv('JIRA_ACTIVE', True)
JIRA_TIMEOUT = int(os.getenv('JIRA_TIMEOUT', 15))
JIRA_TEMP_FILES = os.getenv('JIRA_TEMP_FILES', '/tmp')

# Skype Bot:
SKYPE_ACTIVE = os.getenv('SKYPE_ACTIVE', True)
SKYPE_USER = os.getenv('SKYPE_USER', '')
SKYPE_PASS = os.getenv('SKYPE_PASS', '')
SKYPE_TEMP_FILES = os.getenv('SKYPE_TEMP_FILES', '/tmp')

# Telegram Bot:
TELEGRAM_ACTIVE = os.getenv('TELEGRAM_ACTIVE', True)
TELEGRAM_TEMP_FILES = os.getenv('TELEGRAM_TEMP_FILES', '/tmp')

# Slack Bot:
SLACK_ACTIVE = os.getenv('SLACK_ACTIVE', True)
SLACK_TEMP_FILES = os.getenv('SLACK_TEMP_FILES', '/tmp')

# Webhook bot:
WEBHOOK_ACTIVE = os.getenv('WEBHOOK_ACTIVE', True)

# Teams Bot
TEAMS_ACTIVE = os.getenv('TEAMS_ACTIVE', True)

# PAGERDUTY Bot
PAGERDUTY_ACTIVE = os.getenv('PAGERDUTY_ACTIVE', True)
PAGERDUTY_ENDPOINT = os.getenv('PAGERDUTY_ENDPOINT', 'https://events.pagerduty.com/v2/enqueue')

# SMS Bot
SMS_ACTIVE = os.getenv('SMS_ACTIVE', True)

# VOICE Bot
VOICE_ACTIVE = os.getenv('VOICE_ACTIVE', True)

# SIGNL4 Bot
SIGNL4_ACTIVE = os.getenv('SIGNL4_ACTIVE', True)

NOTIFICATION_TYPE_MAPPING = {
    "ui": 1,
    "email": 2,
    "jira": 3,
    "skype": 4,
    "teams": 5,
    "telegram": 6,
    "pagerduty": 7,
    "sms": 8,
    "voice": 9,
    "whatsapp": 10,
    "signl4": 11,
    "slack": 12,
    "webhook": 13
}

NOTIFICATION_STATUS_MAPPING = {
    0: "ok",
    1: "alert",
    2: "new",
    3: "flapping",
    4: "urgent",
    5: "test"
}

SEVERITY_MAPPING = {
    0: "ok",
    1: "information",
    2: "warning",
    3: "critical",
    4: "unknown",
    5: "urgent",
    6: "down"
}

GRAFANA_RENDER_USER = os.getenv('GRAFANA_RENDER_USER', 'some_user')
GRAFANA_RENDER_PASS = os.getenv('GRAFANA_RENDER_PASS', 'some_pass')

ZABBIX_RENDER_USER = os.getenv('ZABBIX_RENDER_USER', 'some_user')
ZABBIX_RENDER_PASS = os.getenv('ZABBIX_RENDER_PASS', 'some_pass')

GRAPH = {
    "default_time_range": "3h",
    "width": 1100
}

CHECK_ALERT_STATE_FLAPPING = os.getenv('CHECK_ALERT_STATE_FLAPPING', True)
DEEP_REPORTING = os.getenv('DEEP_REPORTING', True)


IGNORE_ALL_MESSAGES = os.getenv('IGNORE_ALL_MESSAGES', True)

DOCKER_SERVER_IP = os.getenv('DOCKER_SERVER_IP', False)