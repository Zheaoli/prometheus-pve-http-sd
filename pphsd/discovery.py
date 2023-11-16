import ipaddress
import re
import time
from threading import Thread
from typing import cast, Literal

from loguru import logger

from pphsd.client import ProxmoxClient
from pphsd.config import Config
from pphsd.exceptions import APIError
from pphsd.model import Host, Hosts
from pphsd.pve_model import NodeDetail, VMDetail, LXCDetail


def _validate_ip(address: str) -> Literal[False] | str:
    try:
        if (
            not ipaddress.ip_address(address).is_loopback
            and not ipaddress.ip_address(address).is_link_local
        ):
            return address
    except ValueError:
        return False
    return False


def _get_names(
    pve_list: list[NodeDetail], pve_type: Literal["node"] | Literal["pool"]
) -> list[str]:
    names = []
    match pve_type:
        case "node":
            names = [node.node for node in pve_list if node.node]
        case "pool":
            names = [pool.poolid for pool in pve_list if pool.poolid]
    return names


class Discovery:
    def __init__(self, config: Config):
        self.config = config
        self.client = ProxmoxClient(config)
        self.hosts = Hosts([])

    def _get_ip_address(
        self, pve_type: Literal["qemu"] | Literal["container"], pve_node: str, vmid: int
    ) -> tuple[str, str]:
        ipv4_address: str = ""
        ipv6_address: str = ""
        if pve_type == "qemu":
            networks = None
            try:
                if self.client.get_agent_info(pve_node, pve_type, vmid) is not None:
                    networks = self.client.get_network_interfaces(pve_node, vmid)
            except Exception:  # noqa
                pass
            if networks:
                for network in networks:
                    for ip_address in network.ip_addresses:
                        if ip_address.ip_address_type == "ipv4" and not ipv4_address:
                            ipv4_address = _validate_ip(ip_address.ip_address)
                        elif ip_address.ip_address_type == "ipv6" and not ipv6_address:
                            ipv6_address = _validate_ip(ip_address.ip_address)
        config = self.client.get_instance_config(pve_node, pve_type, vmid)
        if config and ipv4_address == "":
            try:
                if "ipconfig0" in config:
                    sources = [config["net0"], config["ipconfig0"]]
                else:
                    sources = [config["net0"]]

                for s in sources:
                    find = re.search(r"ip=(\d*\.\d*\.\d*\.\d*)", str(s))
                    if find and find.group(1):
                        ipv4_address = find.group(1)
                        break
            except Exception:  # noqa
                pass
        if config and ipv6_address == "":
            try:
                if "ipconfig0" in config:
                    sources = [config["net0"], config["ipconfig0"]]
                else:
                    sources = [config["net0"]]

                for s in sources:
                    find = re.search(
                        r"ip=(([a-fA-F0-9]{0,4}:{0,2}){0,7}:[0-9a-fA-F]{1,4})", str(s)
                    )
                    if find and find.group(1):
                        ipv6_address = find.group(1)
                        break
            except Exception:  # noqa
                pass

        return cast(tuple[str, str], (ipv4_address, ipv6_address))

    def _filer(
        self, pve_list: list[VMDetail] | list[LXCDetail]
    ) -> list[VMDetail | LXCDetail]:
        results = []
        for item in pve_list:
            if (
                len(self.config.include_vmid)
                and str(item.vmid) not in self.config.include_vmid
            ):
                continue
            if len(self.config.include_tags) and (
                bool(item.tags) is False
                or (
                    item.tags
                    and set(item.tags.split(",")).isdisjoint(self.config.include_tags)
                )
            ):
                continue
            if isinstance(item, VMDetail) and item.template == 1:
                continue
            if item.status in self.config.exclude_state:
                continue
            if item.vmid in self.config.exclude_vmid:
                continue
            if len(self.config.exclude_tags) and (
                bool(item.tags) is False
                or not (
                    item.tags
                    and set(item.tags.split(",")).isdisjoint(self.config.include_tags)
                )
            ):
                continue
            results.append(item)
        return results

    def discovery(self) -> Hosts:
        self.hosts.clear()
        nodes = _get_names(self.client.get_nodes(), "node")
        logger.info(f"found nodes: {nodes}")
        for node in nodes:
            try:
                vms = self._filer(self.client.get_all_vms(node))
                containers = self._filer(self.client.get_all_containers(node))
            except Exception as e:
                raise APIError(str(e)) from e
            for vm in vms + containers:
                if vm.name:
                    vmid = vm.vmid
                    pve_type: Literal["qemu"] | Literal["container"] = cast(
                        Literal["qemu"] | Literal["container"],
                        ("qemu" if isinstance(vm, VMDetail) else "container"),
                    )
                    config = self.client.get_instance_config(node, pve_type, vmid)
                    try:
                        description = config["description"]
                    except KeyError:
                        description = None
                    except Exception as e:  # noqa
                        raise APIError(str(e)) from e
                    ipv4_address, ipv6_address = self._get_ip_address(
                        pve_type, node, vmid
                    )
                    host = Host(
                        hostname=vm.name,
                        ipv4_address=ipv4_address,
                        ipv6_address=ipv6_address,
                        vmid=vmid,
                        pve_type=pve_type,
                        labels={},
                    )
                    config_flags = [
                        ("cpu", "sockets"),
                        ("cores", "cores"),
                        ("memory", "memory"),
                    ]
                    for key, flag in config_flags:
                        if flag in config:
                            host.add_label(key, config[flag])
                    host.add_label("status", vm.status)
                    host.add_label("tags", vm.tags)
                    self.hosts.add_host(host)
        return self.hosts

    def run(self) -> None:
        while True:
            self.discovery()
            time.sleep(self.config.interval)
