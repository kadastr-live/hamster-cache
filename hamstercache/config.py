import urllib.parse
import logging
from hashlib import md5
from pathlib import Path

import crossplane
import yaml
from pydantic import BaseModel, Field, ValidationError
from .models import Config


def validate_config(config_data):
    try:
        config = Config(**config_data)
    except ValidationError as e:
        raise
    return config


def load_config(file_path):
    with open(file_path, 'r') as file:
        config_data = yaml.safe_load(file)
    return validate_config(config_data)


def generate_proxy_paths(config):
    proxy_paths = []
    for proxy in config.proxies:
        proxy_paths.append({
            "directive": "proxy_cache_path",
            "args": [f"/cache/{proxy.hash()}", f"keys_zone={proxy.hash()}:{proxy.cache.size}"]
        })
        proxy_paths.append({
            "directive": "#",
            "comment": proxy.url
        })
    return proxy_paths


def generate_locations(config):
    locations = []
    for proxy in config.proxies:
        locations.append({
            "directive": "location",
            "args": [proxy.location()],
            "block": [
                {
                    "directive": "proxy_pass",
                    "args": [proxy.url]
                },
                {
                    "directive": "proxy_cache",
                    "args": [proxy.hash()]
                },
                {
                    "directive": "proxy_cache_key",
                    "args": ['$scheme$proxy_host$uri$is_args$args']
                },
                {
                    "directive": "proxy_cache_valid",
                    "args": ['200', proxy.cache.ttl]
                },
                {
                    "directive": "proxy_cache_use_stale",
                    "args": ['error', 'timeout', 'invalid_header', 'updating', 'http_500', 'http_502', 'http_503',
                             'http_504']
                },
                {
                    "directive": "proxy_hide_header",
                    "args": ['Set-Cookie']
                },
                {
                    "directive": "proxy_pass_request_headers",
                    "args": ['off']
                },
                {
                    "directive": "add_header",
                    "args": ['X-Debug-Cache-Group', proxy.hash()]
                },
            ]
        })
    return locations


def create_nginx_config(config_file):
    config = load_config(config_file)
    logging.debug("Config loaded %s", config)

    proxy_paths = generate_proxy_paths(config)
    locations = generate_locations(config)

    result = crossplane.build([
        {
            "directive": "user",
            "args": ["nginx"],
        },
        {
            "directive": "worker_processes",
            "args": ["auto"],
        },
        {
            "directive": "events",
            "args": [],
            "block": [
                {
                    "directive": "worker_connections",
                    "args": ["1024"],
                },
            ]
        },
        {
            "directive": "error_log",
            "args": ["/dev/stdout", "info"]
        },
        {
            "directive": "http",
            "args": [],
            "block": [
                {
                    "directive": "access_log",
                    "args": ["/dev/stdout"]
                },
                *proxy_paths,
                {
                    "directive": "server",
                    "args": [],
                    "block": [
                        {
                            "directive": "listen",
                            "args": ["80"]
                        },
                        {
                            "directive": "server_name",
                            "args": ["default"]
                        },
                        *locations
                    ]
                }
            ]
        }])
    return result
