import json
import shutil
import tempfile
import time
import tomllib
from os import chmod

import rich_click as click
from flask import Flask, jsonify, Response
from loguru import logger
from pydantic.json import pydantic_encoder

from pphsd.config import Config
from pphsd.discovery import Discovery


def serve_http(config: Config, discovery: Discovery):
    app = Flask(__name__)

    @app.route("/targets")
    def targets():
        hosts = discovery.discovery()
        return jsonify([host.to_sd_json() for host in hosts.hosts])

    app.run(host=config.http_address, port=config.http_port)


def serve_file(config: Config, discovery: Discovery):
    while True:
        hosts = discovery.discovery()
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", prefix="prometheus-pve-sd", delete=False
        )
        with temp_file as tf:
            json.dump([host.to_sd_json() for host in hosts.hosts], tf, indent=4)

        shutil.move(temp_file.name, config.output_file)
        chmod(
            config.output_file,
            int(config.output_file_mode, 8),
        )
        time.sleep(config.interval)


@click.command()
@click.option("-c", "--config", help="config file", type=click.Path(exists=True))
@click.option("-o", "--output", help="output file", type=click.Path(exists=True))
@click.option("--file-mode", help="output file mode", type=str)
@click.option("-m", "--mode", help="serve mode", type=str)
@click.option("-d", "--delay", help="delay between discovery runs", type=int)
def main(config, output, file_mode, mode, delay):
    config_data = None
    if config and config != "":
        logger.info(f"config file: {config}")
        with open(config, "r") as f:
            config_data = Config.model_validate(tomllib.load(f))
    else:
        config_data = Config()
    if output != "":
        logger.info(f"output file: {output}")
        config_data.output_file = output
    if file_mode != "":
        logger.info(f"output file mode: {file_mode}")
        config_data.output_file_mode = file_mode
    if mode != "":
        logger.info(f"serve mode: {mode}")
        config_data.serve_mode = mode
    discovery = Discovery(config_data)
    # thread = Thread(target=discovery.run, args=(), daemon=True)
    # thread.start()
    if mode == "http":
        serve_http(config_data, discovery)
    elif mode == "file":
        serve_file(config_data, discovery)


if __name__ == "__main__":
    main()
