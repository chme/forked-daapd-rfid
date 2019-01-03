
from aiohttp import web, WSMsgType
import asyncio

class WebServer:

    def __init__(self, loop, conf):
        self.loop = loop
        self.forked_daapd_url = 'http://' + conf.get('forked-daapd', 'host') + ':' + conf.get('forked-daapd', 'port')
        self.app = web.Application(loop=loop)
        self.app.add_routes([
                        web.get('/', self.index),
                        web.get('/api/conf', self.api_conf),
                        web.get('/api/tags', self.api_tags),
                        web.post('/api/tags/create', self.api_tags_create),
                        web.get('/ws', self.websocket)])
        self.app.router.add_static(
                        '/static/',
                        path='htdocs/static',
                        name='static')

        self.websockets = []

        self.runner = web.AppRunner(self.app)

    def start(self):
        self.loop.run_until_complete(self.runner.setup())
        self.site = web.TCPSite(self.runner, '0.0.0.0', 9090)
        self.loop.run_until_complete(self.site.start())

    def cleanup(self):
        self.loop.run_until_complete(self.close_ws())
        self.loop.run_until_complete(self.runner.cleanup())

    def set_rfid(self, rfid):
        self.rfid_reader = rfid

    def get_sitename(self):
        return self.site.name

    async def index(self, request):
        return web.FileResponse('htdocs/index.html')

    async def api_conf(self, request):
        data = { 'server': self.forked_daapd_url }
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
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' % ws.exception())

        self.websockets.remove(ws)

        return ws

    async def close_ws(self):
        for ws in self.websockets:
            await ws.close()

    async def send(self, message):
        for ws in self.websockets:
            await ws.send_str(message)
