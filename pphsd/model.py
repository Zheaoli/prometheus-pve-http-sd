from typing import Optional

from pydantic import dataclasses


@dataclasses.dataclass
class Host:
    hostname: str
    ipv4_address: Optional[str]
    ipv6_address: Optional[str]
    vmid: int
    pve_type: str
    labels: dict[str, str]

    def __str__(self):
        return (
            f"{self.hostname}({self.vmid}): "
            f"{self.pve_type} {self.ipv4_address} {self.ipv6_address}"
        )

    def add_label(self, key, value):
        key = key.replace("-", "_").replace(" ", "_")
        self.labels[f"__meta_pve_{key}"] = str(value)

    def __post_init__(self):
        self.add_label("ipv4", self.ipv4_address)
        self.add_label("ipv6", self.ipv6_address)
        self.add_label("name", self.hostname)
        self.add_label("type", self.pve_type)
        self.add_label("vmid", self.vmid)

    def to_sd_json(self):
        return {"targets": [self.hostname], "labels": self.labels}


@dataclasses.dataclass
class Hosts:
    hosts: list[Host]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        if len(other.hosts) != len(self.hosts):
            return False

        for host in self.hosts:
            if other.host_exists(host):
                continue
            return False

        return True

    def clear(self):
        self.hosts = []

    def add_host(self, host: Host):
        if not self.host_exists(host):
            self.hosts.append(host)

    def host_exists(self, host: Host) -> bool:
        """Check if a host is already in the list by id and type."""
        for current in self.hosts:
            if current.pve_type == host.pve_type and current.vmid == host.vmid:
                return True
        return False
