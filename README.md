## Harp Daemon Service

### Intro
The backend service of Harp Platform and works as engine for process alerts.

Responsible for reading alert from Kafka topic (produced by harp-alert-decorator), describe the logic and state of the alert and write result to MariaDB
