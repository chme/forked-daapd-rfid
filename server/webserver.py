
from aiohttp import web, WSMsgType
import asyncio
import logging

log = logging.getLogger('main')


class WebSocket:

    def __init__(self):
        self.websockets = []

    async def websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        log.debug('[ws] New web socket connection')
        self.websockets.append(ws)

        async for msg in ws:
            log.debug('[ws] New message from websocket with type={0} and data={0}'.format(msg.type, msg.data))
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
            elif msg.type == WSMsgType.ERROR:
                log.debug('[ws] Connection closed with exception %s' % ws.exception())

        log.debug('[ws] Websocket connection closed')
        self.websockets.remove(ws)

        return ws

    async def close(self):
        log.debug('[ws] Close websocket connections')
        for ws in self.websockets:
            await ws.close()
        self.websockets = []

    async def send_current_tag(self, uid, content):
        await self.send({ 'type': 'current_tag', 'current_tag': { 'id': uid, 'content': content } })

    async def send_message(self, uid, text):
        await self.send({ 'type': 'message', 'message': { 'id': uid, 'text': text } })

    async def send(self, message):
        log.debug('[ws] Send message={0}'.format(message))
        for ws in self.websockets:
            await ws.send_json(message)

class WebServer:

    def __init__(self, loop, web_socket, rfid, host, port, daapd_host, daapd_port):
        self.loop = loop
        self.web_socket = web_socket
        self.rfid_reader = rfid

        self.host = host
        self.port = port
        self.daapd_host = daapd_host
        self.daapd_port = daapd_port

        self.app = web.Application(loop=loop)
        self.app.add_routes([
                        web.get('/', self.index),
                        web.get('/api/conf', self.api_conf),
                        web.get('/api/tags/current', self.api_tags_current),
                        web.post('/api/tags/create', self.api_tags_create),
                        web.get('/ws', self.web_socket.websocket)])
        self.app.router.add_static(
                        '/static/',
                        path='htdocs/static',
                        name='static')

        self.websockets = []

        self.runner = web.AppRunner(self.app)

    def start(self):
        log.debug('[web] Starting webserver ...')
        self.loop.run_until_complete(self.runner.setup())
        self.site = web.TCPSite(self.runner, self.host, self.port)
        self.loop.run_until_complete(self.site.start())
        log.info('[web] Webserver running on {}'.format(self.site.name))

    def cleanup(self):
        log.debug('[web] Webserver cleanup ...')
        self.loop.run_until_complete(self.web_socket.close())
        self.loop.run_until_complete(self.runner.cleanup())
        log.debug('[web] Webserver cleanup complete')

    async def index(self, request):
        return web.FileResponse('htdocs/index.html')

    async def api_conf(self, request):
        data = { 'daapd_host': self.daapd_host, 'daapd_port': self.daapd_port }
        return web.json_response(data)

    async def api_tags_current(self, request):
        uid, content = self.rfid_reader.current_tag()
        return web.json_response({ 'id': uid, 'content': content })

    async def api_tags_create(self, request):
        try:
            tag = await request.json()
            log.info('[web] Create new tag request for content={}'.format(tag['content']))
            await self.rfid_reader.write_tag(tag['content'])
            log.info('[web] Tag created')
            return web.json_response({ 'content' : 'xx' })
        except asyncio.CancelledError:
            log.warning('[web] Creating new tag task canceled')
