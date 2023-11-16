from prometheus_client import Gauge, Summary, Counter

PROPAGATION_TIME = Summary(
    "pve_sd_propagate_seconds", "Time spent propagating the inventory from PVE"
)
HOST_GAUGE = Gauge("pve_sd_hosts", "Number of hosts discovered by PVE SD")
PVE_REQUEST_COUNT_TOTAL = Counter(
    "pve_sd_requests_total", "Total count of requests to PVE API"
)
PVE_REQUEST_COUNT_ERROR_TOTAL = Counter(
    "pve_sd_requests_error_total", "Total count of failed requests to PVE API"
)
