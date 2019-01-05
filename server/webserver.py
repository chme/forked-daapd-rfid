
from aiohttp import web, WSMsgType
import asyncio


class WebSocket:

    def __init__(self):
        self.websockets = []

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

    async def close(self):
        for ws in self.websockets:
            await ws.close()

    async def send(self, message):
        for ws in self.websockets:
            await ws.send_str(message)
        self.websockets = []

class WebServer:

    def __init__(self, loop, web_socket, conf):
        self.loop = loop
        self.web_socket = web_socket
        self.forked_daapd_url = 'http://' + conf.get('forked-daapd', 'host') + ':' + conf.get('forked-daapd', 'port')
        self.app = web.Application(loop=loop)
        self.app.add_routes([
                        web.get('/', self.index),
                        web.get('/api/conf', self.api_conf),
                        web.get('/api/tags', self.api_tags),
                        web.post('/api/tags/create', self.api_tags_create),
                        web.get('/ws', self.web_socket.websocket)])
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
        self.loop.run_until_complete(self.web_socket.close())
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
        try:
            tag = await request.json()
            print('Create tag: ', tag)
            await self.rfid_reader.write_tag(tag['content'])
            return web.json_response({ 'content' : 'xx' })
        except asyncio.CancelledError:
            print('Cancel CREATE') # TODO
