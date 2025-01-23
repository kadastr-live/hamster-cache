import urllib.parse
from hashlib import md5

from pydantic import BaseModel, Field


class CacheSettings(BaseModel):
    ttl: str
    size: str = '128M'


class ProxyConfig(BaseModel):
    url: str
    cache: CacheSettings

    def location(self):
        return urllib.parse.urlparse(self.url).path

    def hash(self):
        return md5(self.url.encode('utf-8')).hexdigest()


class Config(BaseModel):
    proxies: list[ProxyConfig]
