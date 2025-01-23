# HamsterCache

HamsterCache is a caching solution with nginx configuration generation and statistics. It provides tools to generate nginx configurations based on a YAML configuration file and to gather statistics about the cache directories.

## Features

- Generate nginx configuration from a YAML file.
- Monitor and reload nginx configuration on changes.
- Gather and display statistics about cache directories.
- Command-line interface using `click`.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/hamstercache.git
    cd hamstercache
    ```

2. Build the Docker image:
    ```sh
    docker build -t hamster-cache .
    ```

## Usage

### Command Line Interface

HamsterCache provides several commands through its CLI:

- `nginx-config`: Generate nginx configuration.
- `statistics`: Display statistics about cache directories.
- `serve`: Start nginx and monitor configuration changes.
- `shell`: Open a shell in the container.

### Example Commands

Generate nginx configuration:
```sh
hamster-cache nginx-config --config-file /etc/hamstercache/config.yaml
```

Display statistics:
```sh
hamster-cache statistics --config-file /etc/hamstercache/config.yaml
```

Start nginx and monitor configuration changes:
```sh
hamster-cache serve --config-file /etc/hamstercache/config.yaml
```

Open a shell in the container:
```sh
hamster-cache shell
```

### Docker Compose

You can use Docker Compose to run HamsterCache:

```yaml
services:
  server:
    build: .
    ports:
      - "127.0.0.1:80:80"
    command:
      - serve
    volumes:
      - ./cache:/cache/
      - ./example/config.yaml:/etc/hamstercache/config.yaml
```

Start the services:
```sh
docker-compose up
```

## Configuration

The configuration file is a YAML file that defines the proxies and cache settings. An example configuration file (`config.yaml`) might look like this:

```yaml
proxies:
  - url: http://example.com
    cache:
      size: 1g
      ttl: 10m
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.