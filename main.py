
import argparse
import asyncio
import configparser
import logging
import logging.config
import sys
from aiohttp import web

from server import webserver, rfidreader, forked_daapd


DEFAULT_CONF_PATH = './musicboxd.conf'
DEFAULT_LOG_PATH  = './musicboxd.log'


def init_log(log_path):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {'format': '%(asctime)s %(levelname)s [%(name)s] %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'default',
                'filename': log_path,
                'encoding': 'utf=8',
                'when': 'D',
                'interval': 7,
                'backupCount': 3
            }
        },
        'loggers': {
            'main': { 'level': 'DEBUG', 'handlers': ['console', 'file'] },
            'aiohttp.access': { 'level': 'DEBUG', 'handlers': ['console', 'file'] },
            'aiohttp.client': { 'level': 'DEBUG', 'handlers': ['console', 'file'] },
            'aiohttp.internal': { 'level': 'DEBUG', 'handlers': ['console', 'file'] },
            'aiohttp.server': { 'level': 'DEBUG', 'handlers': ['console', 'file'] },
            'aiohttp.web': { 'level': 'DEBUG', 'handlers': ['console', 'file'] },
            'aiohttp.websocket': { 'level': 'DEBUG', 'handlers': ['console', 'file'] }
        },
        'disable_existing_loggers': True
    })

    return logging.getLogger('main')

def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-c', '--conf', default=DEFAULT_CONF_PATH, help="Path to the config file")
    parser.add_argument('-l', '--log', default=DEFAULT_LOG_PATH, help="Path to the log file")
    return parser.parse_args()

def main():
    args = parse_args()

    log = init_log(args.log)
    log.info("Starting musicboxd with arguments '%s'", vars(args))


    conf = configparser.ConfigParser(defaults={})
    conf.read(args.conf)

    loop = asyncio.get_event_loop()

    web_socket = webserver.WebSocket()
    web_server = webserver.WebServer(loop, web_socket, conf)

    try:
        web_server.start()

        daapd = forked_daapd.ForkedDaapd(loop,
                                         conf.get('forked-daapd', 'host'),
                                         conf.get('forked-daapd', 'port'),
                                         conf.get('forked-daapd', 'websocket_port'))
        asyncio.ensure_future(daapd.notify_loop(), loop=loop)

        rfid_reader = rfidreader.RfidReader(loop, daapd, web_socket)
        asyncio.ensure_future(rfid_reader.read_tags(), loop=loop)

        web_server.set_rfid(rfid_reader)

        try:
            print("======== Running on {} ========\n"
                  "(Press CTRL+C to quit)".format(web_server.get_sitename()))
            loop.run_forever()
        except (KeyboardInterrupt):
            pass
    finally:
        web_server.cleanup()
        tasks = asyncio.gather(
                    *asyncio.Task.all_tasks(loop=loop),
                    loop=loop,
                    return_exceptions=True)
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()
    if sys.version_info >= (3, 6):
        if hasattr(loop, 'shutdown_asyncgens'):
            loop.run_until_complete(loop.shutdown_asyncgens())

if __name__ == '__main__':
    main()
