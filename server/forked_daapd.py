
import asyncio
import aiohttp
import logging

log = logging.getLogger('main')

class ForkedDaapd:

    def __init__(self, loop, host, port, websocket_port):
        self.loop = loop

        self.host = host
        self.port = port
        self.websocket_port = websocket_port
        self.url = 'http://{0}:{1}'.format(host, port)
        self.websocket_url = 'http://{0}:{1}'.format(host, websocket_port)

        self.client = loop.run_until_complete(self.__create_session())

    async def __create_session(self):
        return aiohttp.ClientSession()

    async def notify_loop(self):
        while True:
            try:
                async with self.client.ws_connect(self.websocket_url, protocols=('notify',)) as ws:
                    log.info('[daapd] Connection to forked-daapd websocket established')
                    await ws.send_json({ 'notify': ['player', 'outputs', 'volume'] })
                    async for msg in ws:
                        print(msg.data)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if msg.data == 'close':
                                await ws.close()
                                break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                log.error('[daapd] Connection to forked-daapd websocket closed')
            except:
                log.error('[daapd] Failed to connect to forked-daapd websocket. Retry in 1 sec.')
                try:
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    log.info('[daapd] Connection retry canceled')
                    await self.client.close()
                    break

        log.error('[daapd] Notify loop closed')

    async def play(self, uri):
        async with self.client.post('{0}/api/queue/items/add?uris={1}&clear=true&shuffle=false&playback=start'.format(self.url, uri)) as resp:
            log.info('[daapd] Play request: {0}'.format(resp.status))

    async def pause(self):
        async with self.client.put('{0}/api/player/pause'.format(self.url)) as resp:
            log.info('[daapd] Pause request: {0}'.format(resp.status))
