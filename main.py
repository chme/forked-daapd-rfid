
import argparse
import asyncio
import configparser
import logging
import logging.config
import sys
import threading

from server import webserver, rfidreader, forked_daapd, buttons, pixels


DEFAULT_CONF_PATH = '/etc/musicbox-daapd.conf'
DEFAULT_LOG_PATH  = '/var/log/musicbox-daapd.log'
DEFAULT_HTDOCS_PATH = '/usr/share/musicbox-daapd/htdocs'

def init_log(log_path):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {'format': '%(asctime)s %(levelname)8s [%(name)s] %(message)s'}
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
            'aiohttp.websocket': { 'level': 'DEBUG', 'handlers': ['console', 'file'] },
            'mfrc522.log': { 'level': 'DEBUG', 'handlers': ['console', 'file'] }
        },
        'disable_existing_loggers': True
    })

    return logging.getLogger('main')

def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-c', '--conf', default=DEFAULT_CONF_PATH, help="Path to the config file")
    parser.add_argument('-l', '--log', default=DEFAULT_LOG_PATH, help="Path to the log file")
    parser.add_argument('-w', '--webroot', default=DEFAULT_HTDOCS_PATH, help="Path to the web root folder (htdocs)")
    return parser.parse_args()

def main():
    args = parse_args()

    log = init_log(args.log)
    log.info('Starting musicboxd with arguments {}'.format(vars(args)))


    conf = configparser.ConfigParser(defaults={})
    conf.read(args.conf)

    _has_pixels = conf.get('pixels').getboolean('enabled')

    loop = asyncio.get_event_loop()

    try:
        if _has_pixels:
            neo_pixels = pixels.Pixels()
            pixel_thread = threading.Thread(target=pixels.neopixels, args=(neo_pixels,))
            pixel_thread.start()
        else:
            neo_pixels = None
        
        web_socket = webserver.WebSocket()

        daapd = forked_daapd.ForkedDaapd(loop,
                                         conf.get('forked-daapd', 'host'),
                                         conf.get('forked-daapd', 'port'),
                                         conf.get('forked-daapd', 'websocket_port'))
        daapd.start()

        rfid_reader = rfidreader.RfidReader(loop,
                                            daapd,
                                            web_socket,
                                            neo_pixels)
        rfid_reader.start()
        btn = buttons.Buttons(loop, daapd, neo_pixels)
        btn.start()

        web_server = webserver.WebServer(loop,
                                         web_socket,
                                         rfid_reader,
                                         args.webroot,
                                         conf.get('server', 'host'),
                                         conf.get('server', 'port'),
                                         conf.get('forked-daapd', 'host'),
                                         conf.get('forked-daapd', 'port'))
        web_server.start()

        try:
            print('(Press CTRL+C to quit)')
            loop.run_forever()
        except (KeyboardInterrupt):
            pass
    finally:
        web_server.cleanup()
        rfid_reader.cleanup()
        btn.cleanup()
        tasks = asyncio.gather(
                    *asyncio.Task.all_tasks(loop=loop),
                    loop=loop,
                    return_exceptions=True)
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()
        if _has_pixels:
            neo_pixels.stop()
            pixel_thread.join()
    if sys.version_info >= (3, 6):
        if hasattr(loop, 'shutdown_asyncgens'):
            loop.run_until_complete(loop.shutdown_asyncgens())

if __name__ == '__main__':
    main()
