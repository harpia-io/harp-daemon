from prometheus_client import Gauge, Counter, Summary, Histogram


class Prom:
    UI_CREATE_NOTIFICATION = Summary('ui_create_notification_latency_seconds', 'Time spent processing create notification')
    UI_UPDATE_NOTIFICATION = Summary('ui_update_notification_latency_seconds', 'Time spent processing update notification')
    UI_RESUBMIT_NOTIFICATION = Summary('ui_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    UI_CLOSE_NOTIFICATION = Summary('ui_close_notification_latency_seconds', 'Time spent processing close notification')
    UI_TRACK_STATISTICS = Summary('ui_track_statistics_latency_seconds', 'Time spent processing track statistics')

    EMAIL_CREATE_NOTIFICATION = Summary('email_create_notification_latency_seconds', 'Time spent processing create notification')
    EMAIL_UPDATE_NOTIFICATION = Summary('email_update_notification_latency_seconds', 'Time spent processing update notification')
    EMAIL_RESUBMIT_NOTIFICATION = Summary('email_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    EMAIL_CLOSE_NOTIFICATION = Summary('email_close_notification_latency_seconds', 'Time spent processing close notification')

    JIRA_CREATE_NOTIFICATION = Summary('jira_create_notification_latency_seconds', 'Time spent processing create notification')
    JIRA_UPDATE_NOTIFICATION = Summary('jira_update_notification_latency_seconds', 'Time spent processing update notification')
    JIRA_RESUBMIT_NOTIFICATION = Summary('jira_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    JIRA_CLOSE_NOTIFICATION = Summary('jira_close_notification_latency_seconds', 'Time spent processing close notification')

    PD_CREATE_NOTIFICATION = Summary('pd_create_notification_latency_seconds', 'Time spent processing create notification')
    PD_UPDATE_NOTIFICATION = Summary('pd_update_notification_latency_seconds', 'Time spent processing update notification')
    PD_CLOSE_NOTIFICATION = Summary('pd_close_notification_latency_seconds', 'Time spent processing close notification')

    SKYPE_CREATE_NOTIFICATION = Summary('skype_create_notification_latency_seconds', 'Time spent processing create notification')
    SKYPE_UPDATE_NOTIFICATION = Summary('skype_update_notification_latency_seconds', 'Time spent processing update notification')
    SKYPE_RESUBMIT_NOTIFICATION = Summary('skype_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    SKYPE_CLOSE_NOTIFICATION = Summary('skype_close_notification_latency_seconds', 'Time spent processing close notification')

    SMS_CREATE_NOTIFICATION = Summary('sms_create_notification_latency_seconds', 'Time spent processing create notification')
    SMS_UPDATE_NOTIFICATION = Summary('sms_update_notification_latency_seconds', 'Time spent processing update notification')
    SMS_RESUBMIT_NOTIFICATION = Summary('sms_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    SMS_CLOSE_NOTIFICATION = Summary('sms_close_notification_latency_seconds', 'Time spent processing close notification')

    TEAMS_CREATE_NOTIFICATION = Summary('teams_create_notification_latency_seconds', 'Time spent processing create notification')
    TEAMS_UPDATE_NOTIFICATION = Summary('teams_update_notification_latency_seconds', 'Time spent processing update notification')
    TEAMS_RESUBMIT_NOTIFICATION = Summary('teams_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    TEAMS_CLOSE_NOTIFICATION = Summary('teams_close_notification_latency_seconds', 'Time spent processing close notification')

    TELEGRAM_CREATE_NOTIFICATION = Summary('telegram_create_notification_latency_seconds', 'Time spent processing create notification')
    TELEGRAM_UPDATE_NOTIFICATION = Summary('telegram_update_notification_latency_seconds', 'Time spent processing update notification')
    TELEGRAM_RESUBMIT_NOTIFICATION = Summary('telegram_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    TELEGRAM_CLOSE_NOTIFICATION = Summary('telegram_close_notification_latency_seconds', 'Time spent processing close notification')

    SLACK_CREATE_NOTIFICATION = Summary('slack_create_notification_latency_seconds', 'Time spent processing create notification')
    SLACK_UPDATE_NOTIFICATION = Summary('slack_update_notification_latency_seconds', 'Time spent processing update notification')
    SLACK_RESUBMIT_NOTIFICATION = Summary('slack_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    SLACK_CLOSE_NOTIFICATION = Summary('slack_close_notification_latency_seconds', 'Time spent processing close notification')

    WEBHOOK_CREATE_NOTIFICATION = Summary('webhook_create_notification_latency_seconds', 'Time spent processing create notification')
    WEBHOOK_UPDATE_NOTIFICATION = Summary('webhook_update_notification_latency_seconds', 'Time spent processing update notification')
    WEBHOOK_RESUBMIT_NOTIFICATION = Summary('webhook_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    WEBHOOK_CLOSE_NOTIFICATION = Summary('webhook_close_notification_latency_seconds', 'Time spent processing close notification')

    VOICE_CREATE_NOTIFICATION = Summary('voice_create_notification_latency_seconds', 'Time spent processing create notification')
    VOICE_UPDATE_NOTIFICATION = Summary('voice_update_notification_latency_seconds', 'Time spent processing update notification')
    VOICE_RESUBMIT_NOTIFICATION = Summary('voice_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    VOICE_CLOSE_NOTIFICATION = Summary('voice_close_notification_latency_seconds', 'Time spent processing close notification')

    SIGNL4_CREATE_NOTIFICATION = Summary('signl4_create_notification_latency_seconds', 'Time spent processing create notification')
    SIGNL4_UPDATE_NOTIFICATION = Summary('signl4_update_notification_latency_seconds', 'Time spent processing update notification')
    SIGNL4_RESUBMIT_NOTIFICATION = Summary('signl4_resubmit_notification_latency_seconds', 'Time spent processing resubmit notification')
    SIGNL4_CLOSE_NOTIFICATION = Summary('signl4_close_notification_latency_seconds', 'Time spent processing close notification')

    # Schedulers
    ALERT_RESUBMIT_PROCESSOR = Summary('alert_resubmit_processor_latency_seconds', 'Time spent processing resubmit')
    ALERT_ASSIGN_PROCESSOR = Summary('alert_assign_processor_latency_seconds', 'Time spent processing assign')
    ENV_DICT_UPDATE_PROCESSOR = Summary('env_dict_update_processor_latency_seconds', 'Time spent processing env dict')
    NOTIFICATION_SCHEDULER_PROCESSOR = Summary('notification_scheduler_processor_latency_seconds', 'Time spent processing scheduled notifications')

    # General metrics
    TOTAL_NOTIFICATION_PROCESSOR = Summary('total_notification_processor_latency_seconds', 'Time spent processing total notifications')
    GRAPH_RENDER_PROCESSOR = Summary('graph_render_processor_latency_seconds', 'Time spent processing render graphs')

    # Describe Alerts details counter
    notification_statistics_by_alert_name = Counter('notification_statistics_by_alert_name', 'Statistics about notifications by alert name', [
        'alert_name', 'ms', 'source', 'object_name', 'notification_action', 'notification_type', 'severity', 'notification_status'
    ])
    notification_statistics_by_labels = Counter('notification_statistics_by_labels', 'Statistics about notifications by labels', [
        'alert_name', 'ms', 'source', 'object_name', 'notification_action', 'notification_type', 'severity', 'label_name', 'label_value'
    ])
    notification_statistics_alert_duration = Gauge('notification_statistics_alert_duration', 'Statistics about alert duration in seconds', [
        'notification_action', 'alert_name', 'ms', 'source'
    ])
