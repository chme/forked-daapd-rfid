import sys
import asyncio
import argparse
import configparser
import logging
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
import RPi.GPIO as GPIO
import aiohttp
from aiohttp import web, WSMsgType
from MFRC522 import SimpleMFRC522


DEFAULT_CONF_PATH = '../musicboxd.conf'
DEFAULT_LOG_PATH = '../musicboxd.log'

conf = None


class RfidReader:

    MODE_READ    = 1
    MODE_WRITE   = 2

    run = True

    tags = []

    def __init__(self, loop):
        global conf
        self.loop = loop
        self.mode = self.MODE_READ
        self.reader = SimpleMFRC522.SimpleMFRC522()
        self.forked_daapd_url = conf.get('musicbox', 'server')
        self.next_tag = None

    def cancel(self):
        self.run = False
        self.reader.cancel_wait()

    def write_next_tag(self, content):
        print('Write next tag: ', content)
        self.next_tag = content
        self.mode = self.MODE_WRITE

    async def handle_tags(self):
        async with aiohttp.ClientSession() as client:
            try:
                while self.run:
                    await self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
                    uid, content = self.reader.read()
                    print('Tag found', uid, content)

                    if uid == None:
                        print('Failed to read tag id')
                        continue

                    if self.mode == self.MODE_READ:
                        await self.play(uid, content, client)
                    elif self.mode == self.MODE_WRITE:
                        self.write_tag(uid, content)
                    else:
                        print('ERR Unknown mode', self.mode)

                    await self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)

            except asyncio.CancelledError:
                print('>>>> CancelledError')

    async def play(self, uid, content, client):
        print('PLAY', id, content)

        self.tags.append({ 'id' : id, 'content' : content })

        async with client.put(self.forked_daapd_url + '/api/queue/clear') as resp:
            assert resp.status == 200
            async with client.put(self.forked_daapd_url + '/api/player/shuffle?state=false') as resp:
                assert resp.status == 200
                async with client.put(self.forked_daapd_url + '/api/queue/items/add?uris=' + content) as resp:
                    assert resp.status == 200
                    async with client.put(self.forked_daapd_url + '/api/player/play') as resp:
                        assert resp.status == 200

    def write_tag(self, uid, content):
        print('WRITE TAG', uid, content)

        if (self.next_tag):
            self.reader.write_text(uid, self.next_tag)

        self.mode = self.MODE_READ
        self.next_tag = None


class WebApi:

    def __init__(self, loop):
        self.loop = loop
        self.app = web.Application(loop=loop)
        self.app.add_routes([
                        web.get('/', self.index),
                        web.get('/api/conf', self.api_conf),
                        web.get('/api/tags', self.api_tags),
                        web.post('/api/tags/create', self.api_tags_create),
                        web.get('/ws', self.websocket)])
        self.app.router.add_static(
                        '/static/',
                        path='../htdocs/static',
                        name='static')

        self.websockets = []

    def get_app(self):
        return self.app

    def set_rfid(self, rfid):
        self.rfid_reader = rfid

    async def index(self, request):
        return web.FileResponse('../htdocs/index.html')

    async def api_conf(self, request):
        global conf
        data = { 'server': conf.get('musicbox', 'server') }
        return web.json_response(data)

    async def api_tags(self, request):
        return web.json_response({ 'tags' : [ { 'id' : 123, 'content' : 'library:album:123' },  { 'id' : 456, 'content' : 'library:album:456' }]})

    async def api_tags_create(self, request):
        tag = await request.json()
        print('Create tag: ', tag)
        self.rfid_reader.write_next_tag(tag['content'])
        asyncio.ensure_future(self.send('Test'), loop=self.loop)
        return web.json_response({ 'content' : 'xx' })

    async def websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websockets.append(ws)

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    await ws.send_str(msg.data + '/answer')
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                ws.exception())

        self.websockets.remove(ws)

        return ws

    async def send(self, message):
        for ws in self.websockets:
            await ws.send_str(message)

def deflog(path):
    log = logging.getLogger('musicboxd')
    log.setLevel(logging.INFO)
    filehandler = TimedRotatingFileHandler(
                path,
                encoding='utf=8',
                when='D',
                interval=7,
                backupCount=8,
              )
    fmtr = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
    global conf

    args = parse_args()

    log = deflog(args.log)
    log.info("Starting musicboxd with arguments '%s'", vars(args))


    conf = configparser.ConfigParser(defaults={})
    conf.read(args.conf)

    loop = asyncio.get_event_loop()

    web_api = WebApi(loop)

    runner = web.AppRunner(web_api.get_app())
    loop.run_until_complete(runner.setup())

    try:
        site = web.TCPSite(runner, '127.0.0.1', 9090)
        loop.run_until_complete(site.start())

        rfid_reader = RfidReader(loop)
        asyncio.ensure_future(rfid_reader.handle_tags(), loop=loop)

        web_api.set_rfid(rfid_reader)

        try:
            print("======== Running on {} ========\n"
                  "(Press CTRL+C to quit)".format(site.name))
            loop.run_forever()
        except (KeyboardInterrupt):
            pass
    finally:
        loop.run_until_complete(runner.cleanup())
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
    try:
        main()
    finally:
        GPIO.cleanup()
        pass
