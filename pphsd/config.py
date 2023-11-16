from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MetricsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="prometheus_pve_http_sd_metrics_", extra="allow"
    )

    enabled: bool = Field(True, env="enabled")
    address: str = Field("127.0.0.1", env="address")
    port: int = Field(8000, env="port")


class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="prometheus_pve_http_sd_logging_", extra="allow"
    )
    level: str = Field("INFO", env="level")


class PVEConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="prometheus_pve_http_sd_pve_", extra="allow"
    )
    server: str = Field("", env="server")
    user: str = Field("", env="user")
    password: str = Field("", env="password")
    auth_timeout: int = Field(5, env="auth_timeout")
    verify_ssl: bool = Field(True, env="verify_ssl")


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="prometheus_pve_http_sd_", extra="allow"
    )
    config_file: str = Field("", env="config_file")
    output_file: str = Field("", env="output_file")
    output_file_mode: str = Field("0640", env="output_file_mode")
    serve_mode: str = Field("http", env="serve_mode")
    service: bool = Field(True, env="service")
    interval: int = Field(10, env="interval")
    http_address: str = Field("0.0.0.0", env="http_address")
    http_port: int = Field(8080, env="http_port")
    exclude_state: list[str] = Field([], env="exclude_state")
    exclude_vmid: list[int] = Field([], env="exclude_vmid")
    include_vmid: list[int] = Field([], env="include_vmid")
    exclude_tags: list[str] = Field([], env="exclude_tags")
    include_tags: list[str] = Field([], env="include_tags")
    metrics_config: MetricsConfig = Field(default_factory=lambda: MetricsConfig())
    logging_config: LoggingConfig = Field(default_factory=lambda: LoggingConfig())
    pve_config: PVEConfig = Field(default_factory=lambda: PVEConfig())
