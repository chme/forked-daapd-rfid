import sys
import asyncio
import configparser
import RPi.GPIO as GPIO
from aiohttp import web, WSMsgType
from MFRC522 import SimpleMFRC522

conf = None


class RfidReader:

    MODE_READ    = 1
    MODE_WRITE   = 2

    run = True

    tags = []

    def __init__(self, loop):
        self.loop = loop
        self.mode = self.MODE_READ
        self.reader = SimpleMFRC522.SimpleMFRC522()

    def cancel(self):
        self.run = False
        self.reader.cancel_wait()

    async def handle_tags(self):
        try:
            while self.run:
                await self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
                uid, content = self.reader.read()
                print('Tag found', uid, content)

                if uid == None:
                    print('Failed to read tag id')
                    continue

                if self.mode == self.MODE_READ:
                    self.play(uid, content)
                elif self.mode == self.MODE_WRITE:
                    self.write_tag(uid, content)
                else:
                    print('ERR Unknown mode', self.mode)

                #await asyncio.sleep(1)
                await self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)

        except asyncio.CancelledError:
            print('>>>> CancelledError')

    def play(self, uid, content):
        self.tags.append({ 'id' : id, 'content' : content })
        print('PLAY', id, content)

    def write_tag(self, uid, content):
        print('WRITE TAG', uid, content)


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

    def get_app(self):
        return self.app

    async def index(self, request):
        return web.FileResponse('../htdocs/index.html')

    async def api_conf(self, request):
        global conf
        data = { 'server': conf.get('musicbox', 'server') }
        return web.json_response(data)

    async def api_tags(self, request):
        return web.json_response({ 'tags' : [ { 'id' : 123, 'content' : 'library:album:123' },  { 'id' : 456, 'content' : 'library:album:456' }]})

    async def api_tags_create(self, request):
        return web.json_response({ 'content' : 'xx' })

    async def websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    await ws.send_str(msg.data + '/answer')
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                ws.exception())

        return ws


def main():
    global conf
    conf = configparser.ConfigParser(defaults={})
    conf.read('../musicboxd.conf')

    loop = asyncio.get_event_loop()

    web_api = WebApi(loop)

    runner = web.AppRunner(web_api.get_app())
    loop.run_until_complete(runner.setup())

    try:
        site = web.TCPSite(runner, '127.0.0.1', 9090)
        loop.run_until_complete(site.start())

        rfid_reader = RfidReader(loop)
        asyncio.ensure_future(rfid_reader.handle_tags(), loop=loop)

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
