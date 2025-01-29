import logging
import requests
import urllib.parse

from concurrent.futures import ThreadPoolExecutor

import tqdm
import mercantile
from pydantic import BaseModel

from hamstercache.models import ProxyConfig


class Meta(BaseModel):
    concurrency: int = 2

    bounds: tuple[float, float, float, float]
    format: str

    min_zoom: int = 0
    max_zoom: int = 14


def _seed_tile(url: str, tile: mercantile.Tile, configuration: Meta, progress_bar: tqdm.tqdm):
    try:
        urlparts = urllib.parse.urlparse(url)
        urlparts = urlparts._replace(netloc='localhost:80', scheme='http')

        tile_url = configuration.format.format(x=tile.x, y=tile.y, z=tile.z)
        seed_url = f"{urllib.parse.urlunparse(urlparts)}{tile_url}"
        r = requests.get(seed_url, headers={'X-Purge-Cache': "1"})
        logging.debug('Seeding %s', seed_url)
        assert r.headers['X-Debug-Cache-Bypass'] == "1", str(r.headers)
    except Exception as e:
        logging.error('Failed to seed tile: %s', e)
    finally:
        progress_bar.update(1)


def seed(url: str, metadata: dict):
    configuration = Meta(**metadata)

    progress_bar = tqdm.tqdm(unit='tiles', total=0)
    for zoom in range(configuration.min_zoom, configuration.max_zoom + 1):
        with ThreadPoolExecutor(max_workers=configuration.concurrency) as pool:
            tiles_gen = mercantile.tiles(
                *configuration.bounds,
                zooms=[zoom]
            )
            progress_bar.total = 0
            progress_bar.set_description('Seeding zoom %s' % zoom)
            for tile in tiles_gen:
                progress_bar.total += 1
                pool.submit(_seed_tile, url, tile, configuration, progress_bar)


def get_nginx_location(proxy: ProxyConfig):
    zoom_to_cache = range(proxy.cache.plugin.metadata['min_zoom'], proxy.cache.plugin.metadata['max_zoom'] + 1)
    zoom_regexp = '|'.join(map(str, zoom_to_cache))

    return {
        "directive": "location",
        "args": ["~", f"^{proxy.location()}({zoom_regexp})"],
        "block": [
            {
                "directive": "proxy_pass",
                "args": [proxy.website()]
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
                "directive": "#",
                "comment": "Handle purging and bypass based on custom headers"
            },
            {
                "directive": "proxy_cache_bypass",
                "args": ["$purge_url"]
            },
            {
                "directive": "add_header",
                "args": ['X-Debug-Cache-Group', proxy.hash()]
            },
            {
                "directive": "add_header",
                "args": ['X-Debug-Cache-Bypass', "$purge_url"]
            },
            {
                "directive": "add_header",
                "args": ['X-Cache-Date', "$upstream_http_date"]
            },
        ]
    }
