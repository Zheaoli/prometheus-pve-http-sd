from typing import Optional

from pydantic import BaseModel, Field
from enum import Enum


class NodeStatus(str, Enum):
    online = "online"
    offline = "offline"
    unknown = "unknown"


class LXCStatus(str, Enum):
    running = "running"
    stopped = "stopped"


class VMStatus(str, Enum):
    running = "running"
    stopped = "stopped"


class NodeDetail(BaseModel):
    node: str
    status: NodeStatus
    cpu: Optional[float]
    level: Optional[str]
    maxcpu: Optional[int]
    maxmem: Optional[int]
    mem: Optional[int]
    ssl_fingerprint: Optional[str]
    uptime: Optional[int]
    poolid: Optional[str] = Field(default="")


class VMDetail(BaseModel):
    vmid: int
    status: VMStatus
    cpus: Optional[int]
    lock: Optional[str] = Field(default_factory=str)
    maxdisk: Optional[int]
    maxmem: Optional[int]
    name: Optional[str]
    pid: Optional[int] = Field(default=0)
    qmpstatus: Optional[str] = Field(default_factory=str)
    running_machine: Optional[str] = Field(alias="running-machine", default_factory=str)
    runnin_qemu: Optional[str] = Field(alias="running-qemu", default_factory=str)
    tags: Optional[str] = Field(default_factory=str)
    uptime: Optional[int]
    template: Optional[int] = Field(default=0)
    description: Optional[str] = Field(default_factory=str)


class LXCDetail(BaseModel):
    vmid: int
    status: LXCStatus
    cpus: Optional[int]
    lock: Optional[str]
    maxdisk: Optional[int]
    maxmem: Optional[int]
    maxswap: Optional[int]
    name: Optional[str]
    tags: Optional[str]
    uptime: Optional[int]
    description: Optional[str] = Field(default_factory=str)


# Network Interface config from Proxmox API
class IPAddress(BaseModel):
    prefix: int
    ip_address_type: str = Field(alias="ip-address-type")
    ip_address: str = Field(alias="ip-address")


class Statistics(BaseModel):
    tx_dropped: int = Field(alias="tx-dropped")
    tx_bytes: int = Field(alias="tx-bytes")
    rx_dropped: int = Field(alias="rx-dropped")
    rx_bytes: int = Field(alias="rx-bytes")
    rx_packets: int = Field(alias="rx-packets")
    tx_errs: int = Field(alias="tx-errs")
    tx_packets: int = Field(alias="tx-packets")
    rx_errs: int = Field(alias="rx-errs")


class NetworkInterfaceConfig(BaseModel):
    hardware_address: Optional[str] = Field(alias="hardware-address")
    name: str
    ip_addresses: list[IPAddress] = Field(alias="ip-addresses", default_factory=list)
    statistics: Optional[Statistics]
