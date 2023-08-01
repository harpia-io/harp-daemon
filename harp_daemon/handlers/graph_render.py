from logger.logging import service_logger
import harp_daemon.settings as settings
import requests
from urllib.parse import urlparse
import traceback
from base64 import b64encode
from harp_daemon.tools.prometheus_metrics import Prom
from harp_daemon.plugins.tracer import get_tracer
from opentelemetry.instrumentation.requests import RequestsInstrumentor

log = service_logger()
tracer_get = get_tracer()
tracer = tracer_get.get_tracer(__name__)
RequestsInstrumentor().instrument()


class GraphAPI(object):
    def __init__(self, graph_url, event_id, monitoring_system, server, alert_name, ms_unique_data, graph_time_range=None):
        self.graph_url = graph_url
        self.server = server
        self.event_id = event_id
        self.monitoring_system = monitoring_system
        self.alert_name = alert_name
        self.ms_unique_data = ms_unique_data
        self.graph_time_range = graph_time_range or settings.GRAPH['default_time_range']

    @tracer.start_as_current_span("_login")
    def _login(self):
        data_api = {"name": settings.ZABBIX_RENDER_USER, "password": settings.ZABBIX_RENDER_PASS, "enter": "Sign in"}

        log.debug(
            msg=f"Perform Login to Zabbix, url: http://{self.server}. data_api: {data_api}",
            extra={"tags": {"event_id": self.event_id}}
        )

        req_cookie = requests.post(
            f"http://{self.server}",
            data=data_api,
            timeout=3
        )
        cookie = req_cookie.cookies
        if len(req_cookie.history) > 1 and req_cookie.history[0].status_code == 302:
            log.error(
                msg=f"Probably the server in your config file has not full URL - {self.server}",
                extra={"tags": {"event_id": self.event_id}}
            )
        if not cookie:
            log.warning(
                msg=f"authorization has failed, url: {self.server}/. Stack: {traceback.format_exc()}",
                extra={"tags": {"event_id": self.event_id}})
            cookie = None

        return cookie

    @tracer.start_as_current_span("generate_zabbix_graph")
    def generate_zabbix_graph(self, title, period, zabbix_item_id=None):
        if self.graph_url is None or 'history.php' in self.graph_url or 'screens.php' in self.graph_url or self.graph_url == '':
            img_url = f"http://{self.server}/chart3.php?period={period}&name={title}&graphtype=0&legend=1" \
                f"&items[0][itemid]={zabbix_item_id}&items[0][sortorder]=0"
        else:
            img_url = self.graph_url.replace("charts.php", f"chart2.php?period={period}&")

        log.debug(msg=f"URL to Zabbix image: {img_url}, Zabbix server: {self.server}",
                 extra={"tags": {"event_id": self.event_id}})

        res = requests.get(img_url, cookies=self._login(), timeout=3)
        res_code = res.status_code

        if res_code == 404:
            log.error(
                msg=f"Can't get image from '{img_url}'",
                extra={"tags": {"event_id": self.event_id}}
            )
            return False
        res_img = res.content

        return {"res_img": b64encode(res_img).decode(), "img_url": img_url}

    @staticmethod
    @tracer.start_as_current_span("time_period_converter")
    def time_period_converter(period):
        if 'h' in period:
            period = int((period.replace("h", ""))) * 3600
        elif 'd' in period:
            period = int((period.replace("d", ""))) * 86400

        return int(period)

    @tracer.start_as_current_span("get_zabbix_graph")
    def get_zabbix_graph(self, zabbix_item_id=None):
        if self.graph_url:
            received_graph_url = urlparse(self.graph_url)
            self.server = received_graph_url.netloc
        elif self.monitoring_system == 'zabbix':
            pass
        else:
            log.error(
                msg=f"Unknown Zabbix Server to get Graph: {self.graph_url, self.server}",
                extra={"tags": {"event_id": self.event_id}}
            )
            exit(1)

        title = requests.utils.quote(self.alert_name)

        render_zabbix_graph = self.generate_zabbix_graph(
            title=title, period=self.time_period_converter(self.graph_time_range),
            zabbix_item_id=zabbix_item_id
        )

        log.debug(msg=f"List of Zabbix graphs and time_ranges: {self.graph_time_range}",
                 extra={"tags": {"event_id": self.event_id}})

        return render_zabbix_graph

    @staticmethod
    @tracer.start_as_current_span("add_auth_to_grafana_link")
    def add_auth_to_grafana_link():
        user_pass = b64encode(bytes(settings.GRAFANA_RENDER_USER + ':' + settings.GRAFANA_RENDER_PASS, "utf-8")).decode()
        log.debug(msg=f"Header was created: {user_pass}")

        return user_pass

    @tracer.start_as_current_span("render_grafana")
    def render_grafana(self):
        render_grafana_link = self.graph_url.replace("/d/", "/render/d-solo/")
        if 'viewPanel' in render_grafana_link:
            render_grafana_link = render_grafana_link.replace('viewPanel', 'panelId')
        if 'from=now' not in render_grafana_link:
            render_grafana_link = render_grafana_link + "&from=now-{0}&to=now".format(self.graph_time_range)

        log.debug(
            msg=f"URL to Grafana image: {render_grafana_link}",
            extra={"tags": {"event_id": self.event_id}}
        )

        try:
            get_content = requests.get(
                url=render_grafana_link,
                headers={"Authorization": f"Basic {self.add_auth_to_grafana_link()}"},
                # proxies={"http": "", "https": ""},
                timeout=10
            )

            log.debug(
                msg=f"Grafana was rendered successfully: {render_grafana_link}",
                extra={"tags": {"event_id": self.event_id}}
            )

            return {"res_img": b64encode(get_content.content).decode(), "img_url": self.graph_url}
        except Exception as err:
            log.warning(
                msg=f"Can`t render Grafana graph: {err}. URL: {render_grafana_link}",
                extra={"tags": {"event_id": self.event_id}}
            )

    @Prom.GRAPH_RENDER_PROCESSOR.time()
    @tracer.start_as_current_span("get_graph")
    def get_graph(self):
        log.debug(msg=f"Graph URL before render: {self.graph_url}", extra={"tags": {"event_id": self.event_id}})
        if self.graph_url:
            log.debug(
                msg="Start rendering graph from GRAPH_URL",
                extra={"tags": {"event_id": self.event_id}}
            )

            if 'grafana' in self.graph_url:
                return self.render_grafana()
            elif 'zabbix' in self.graph_url:
                return self.get_zabbix_graph()
        elif self.monitoring_system == 'zabbix':
            zabbix_item_id = self.ms_unique_data['zabbix']['item.id1']
            log.debug(
                msg="Start rendering graph from zabbix item: {0}".format(zabbix_item_id),
                extra={"tags": {"event_id": self.event_id}}
            )
            return self.get_zabbix_graph(zabbix_item_id)
        else:
            return None
