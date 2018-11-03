import asyncio
import configparser
#import RPi.GPIO as GPIO
from aiohttp import web, WSMsgType
from MFRC522 import SimpleMFRC522

conf = None


class RfidReader:

    MODE_READ    = 1
    MODE_WRITE   = 2
    MODE_SUSPEND = 3

    tags = []

    def __init__(self, loop):
        self.loop = loop
        self.mode = self.MODE_SUSPEND
        self.reader = SimpleMFRC522()

    async def wait(self):
        await self.loop.run_in_executor(None, self.reader.wait)
        await self.handle_tag()
        await asyncio.sleep(1)
        asyncio.ensure_future(self.wait(), loop=self.loop)

    async def handle_tag(self):
        id, content = self.reader.read_no_block()
        tags.append({ 'id' : id, 'content' : content })

    def read_tag(self):
        id, content = self.reader.read_no_block()
        tags.append({ 'id' : id, 'content' : content })


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

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '127.0.0.1', 9090)
        await site.start()

    async def stop(self):
        await self.runner.cleanup()

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
    asyncio.ensure_future(web_api.start(), loop=loop)


    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        tasks = asyncio.gather(
                    *asyncio.Task.all_tasks(loop=loop),
                    loop=loop,
                    return_exceptions=True)
        tasks.add_done_callback(lambda t: loop.stop())
        tasks.cancel()

if __name__ == '__main__':
    try:
        main()
    finally:
        #GPIO.cleanup()
        pass
