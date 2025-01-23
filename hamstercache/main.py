import os
import signal
import sys
import logging
import subprocess

import click
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from hamstercache import config, statistics as stats


@click.command()
@click.option('--config-file', default='/etc/hamstercache/config.yaml', help='Path to the configuration file.')
def nginx_config(config_file):
    result = config.create_nginx_config(config_file)

    print(result)


@click.command()
@click.option('--config-file', default='/etc/hamstercache/config.yaml', help='Path to the configuration file.')
def statistics(config_file):
    # Placeholder for statistics functionality
    cfg = config.load_config(config_file)

    _hash_to_name = {
        proxy.hash(): proxy.url for proxy in cfg.proxies
    }
    
    directory_sizes = stats.get_directory_sizes()
    
    # Print the directory sizes in table format
    print(f"{'Name':<80} {'Directory':<30} {'Size':>15}")
    print("-" * 85)
    for entry in directory_sizes:
        print(f"{_hash_to_name.get(entry['name'], 'n/a'):<80} {entry['name']:<30} {entry['size_readable']:>15}")


@click.command()
@click.option('--config-file', default='/etc/hamstercache/config.yaml', help='Path to the configuration file.')
def serve(config_file: str):
    logging.info('Starting server and watching for config changes')

    def recreate_nginx_config():
        result = config.create_nginx_config(config_file)

        with open('/etc/nginx/nginx.conf', 'w') as f:
            f.write(result)

    recreate_nginx_config()
    p = subprocess.Popen(['nginx', '-g', 'daemon off;'])

    class ConfigChangeHandler(FileSystemEventHandler):
        def on_modified(self, event):
            logging.info('File %s has been modified', event.src_path)
            try:
                recreate_nginx_config()
            except Exception:
                logging.exception('Unable to recreate config')
            else:
                logging.info('Reloading nginx pid=%s', p.pid)
                os.kill(p.pid, signal.SIGHUP)

    event_handler = ConfigChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=config_file, recursive=False)
    observer.start()

    try:
        p.wait()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


@click.command()
def shell():
    p = subprocess.Popen(['sh'], stdin=sys.stdin)
    p.wait()


@click.group()
def cli():
    logging.basicConfig(level=logging.INFO, force=True)
    logging.info('Starting up')


cli.add_command(nginx_config)
cli.add_command(statistics)
cli.add_command(serve)
cli.add_command(shell)

if __name__ == '__main__':
    cli()
