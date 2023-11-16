from typing import Any, cast

import requests
from loguru import logger
from proxmoxer import ProxmoxAPI

from pphsd.config import Config
from pphsd.exceptions import APIError
from pphsd.metrics import PVE_REQUEST_COUNT_ERROR_TOTAL, PVE_REQUEST_COUNT_TOTAL
from pphsd.pve_model import LXCDetail, NetworkInterfaceConfig, NodeDetail, VMDetail


class ProxmoxClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = self._auth()

    def _auth(self):
        try:
            logger.debug(
                "Trying to authenticate against {} as user {}".format(
                    self.config.pve_config.server, self.config.pve_config.user
                )
            )
            return ProxmoxAPI(
                self.config.pve_config.server,
                user=self.config.pve_config.user,
                password=self.config.pve_config.password,
                verify_ssl=self.config.pve_config.verify_ssl,
                timeout=self.config.pve_config.auth_timeout,
            )
        except requests.RequestException as e:
            PVE_REQUEST_COUNT_ERROR_TOTAL.inc()
            raise APIError(str(e)) from e

    def _do_request(self, *args) -> Any:
        PVE_REQUEST_COUNT_TOTAL.inc()
        try:
            # create a new tuple containing nodes and unpack it again for client.get
            return self.client.get(*("nodes", *args))
        except requests.RequestException as e:
            PVE_REQUEST_COUNT_ERROR_TOTAL.inc()
            raise APIError(str(e)) from e

    def get_nodes(self) -> list[NodeDetail]:
        logger.debug("fetching all nodes")
        response = cast(list[dict[str, Any]], self._do_request())
        return [NodeDetail.model_validate(node) for node in response]

    def get_all_vms(self, pve_node: str) -> list[VMDetail]:
        logger.debug(f"fetching all vms on node {pve_node}")
        response = cast(list[dict[str, Any]], self._do_request(pve_node, "qemu"))
        return [VMDetail.model_validate(host) for host in response]

    def get_all_containers(self, pve_node: str) -> list[LXCDetail]:
        logger.debug(f"fetching all containers on node {pve_node}")
        response = cast(list[dict[str, Any]], self._do_request(pve_node, "lxc"))
        return [LXCDetail.model_validate(container) for container in response]

    def get_instance_config(
        self, pve_node: str, pve_type: str, vmid: int
    ) -> dict[str, Any]:
        logger.debug(f"fetching instance config for {vmid} on {pve_node}")
        return self._do_request(pve_node, pve_type, vmid, "config")

    def get_agent_info(self, pve_node: str, pve_type: str, vmid: int) -> Any:
        logger.debug(f"fetching agent info for {vmid} on {pve_node}")
        return self._do_request(pve_node, pve_type, vmid, "agent", "info")["result"]

    def get_network_interfaces(
        self, pve_node: str, vmid: int
    ) -> list[NetworkInterfaceConfig]:
        logger.debug(f"fetching network interfaces for {vmid} on {pve_node}")
        response = cast(
            list[dict[str, Any]],
            self._do_request(pve_node, "qemu", vmid, "agent", "network-get-interfaces")[
                "result"
            ],
        )
        return [NetworkInterfaceConfig.model_validate(network) for network in response]


if __name__ == "__main__":
    config = Config().model_validate(
        {
            "pve_config": {
                "server": "192.168.11.1:8006",
                "user": "root@pam",
                "password": "3550489",
                "verify_ssl": False,
            }
        }
    )
    client = ProxmoxClient(config)
    print(client.get_nodes())
    print(client.get_all_vms("manjusaka3"))
