from hamstercache.models import ProxyConfig


def get_nginx_location(proxy: ProxyConfig):
    return {
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
