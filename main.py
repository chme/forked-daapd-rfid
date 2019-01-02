
import argparse
import asyncio
import configparser
import logging
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
import sys
from aiohttp import web

from server import webserver, rfidreader


DEFAULT_CONF_PATH = './musicboxd.conf'
DEFAULT_LOG_PATH  = './musicboxd.log'


def deflog(path):
    log = logging.getLogger('musicboxd')
    log.setLevel(logging.INFO)

    fmtr = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    filehandler = TimedRotatingFileHandler(
                path,
                encoding='utf=8',
                when='D',
                interval=7,
                backupCount=8,
              )
    filehandler.setFormatter(fmtr)
    log.addHandler(filehandler)

    syserrhandler = StreamHandler()
    syserrhandler.setFormatter(fmtr)
    log.addHandler(syserrhandler)

    return log

def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-c', '--conf', default=DEFAULT_CONF_PATH, help="Path to the config file")
    parser.add_argument('-l', '--log', default=DEFAULT_LOG_PATH, help="Path to the log file")
    return parser.parse_args()

def main():
    args = parse_args()

    log = deflog(args.log)
    log.info("Starting musicboxd with arguments '%s'", vars(args))


    conf = configparser.ConfigParser(defaults={})
    conf.read(args.conf)

    loop = asyncio.get_event_loop()

    web_server = webserver.WebServer(loop, conf)

    try:
        web_server.start()

        rfid_reader = rfidreader.RfidReader(loop, conf)
        asyncio.ensure_future(rfid_reader.handle_tags(), loop=loop)

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
        rfid_reader.cancel()
    if sys.version_info >= (3, 6):
        if hasattr(loop, 'shutdown_asyncgens'):
            loop.run_until_complete(loop.shutdown_asyncgens())

if __name__ == '__main__':
    main()
