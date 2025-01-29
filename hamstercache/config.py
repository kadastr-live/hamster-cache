import logging

import crossplane
import yaml
from pydantic import ValidationError
from .models import Config
from . import plugins


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
            "args": [
                f"/cache/{proxy.hash()}",
                f"keys_zone={proxy.hash()}:{proxy.cache.size}",
                f"inactive={proxy.cache.ttl}"
            ]
        })
        proxy_paths.append({
            "directive": "#",
            "comment": proxy.url
        })
    return proxy_paths


def generate_locations(config):
    locations = []

    for proxy in config.proxies:
        try:
            plugin_instance = getattr(plugins, proxy.cache.plugin.name)
        except AttributeError:
            logging.error('Unable to import plugin `%s`. '
                          'Make sure that it is importable and exists in PYTHONPATH.', proxy.cache.plugin.name)
            raise
        locations.append(plugin_instance.get_nginx_location(proxy))
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
                    "directive": "map",
                    "args": ["$remote_addr", "$purge_allowed"],
                    "block": [
                        {
                            "directive": "default",
                            "args": ["0"]
                        },
                        {
                            "directive": "127.0.0.1",
                            "args": ["1"]
                        }
                    ]
                },

                {
                    "directive": "map",
                    "args": ["$http_x_purge_cache", "$purge_url"],
                    "block": [
                        {
                            "directive": "default",
                            "args": ["0"]
                        },
                        {
                            "directive": "1",
                            "args": ["$purge_allowed"]
                        }
                    ]
                },
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
