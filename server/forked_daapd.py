
import asyncio
import logging

import aiohttp


log = logging.getLogger('main')

class ForkedDaapd:

    def __init__(self, loop, host, port, websocket_port):
        self.loop = loop

        self.host = host
        self.port = port
        self.websocket_port = websocket_port
        self.url = 'http://{0}:{1}'.format(host, port)
        self.websocket_url = 'http://{0}:{1}'.format(host, websocket_port)
        
        self.client = None
        self.connected = False

    def start(self):
        self.client = self.loop.run_until_complete(self.__create_session())
        asyncio.ensure_future(self.notify_loop(), loop=self.loop)

    async def __create_session(self):
        return aiohttp.ClientSession()

    async def notify_loop(self):
        while True:
            try:
                log.debug('[daapd] Connecting to forked-daapd websocket on url={}'.format(self.websocket_url))
                async with self.client.ws_connect(self.websocket_url, protocols=('notify',)) as ws:
                    log.info('[daapd] Connection to forked-daapd websocket established')
                    self.connected = True
                    await ws.send_json({ 'notify': ['player', 'outputs', 'volume'] })
                    async for msg in ws:
                        log.debug('[daapd] New message from websocket with type={0} and data={0}'.format(msg.type, msg.data))
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if msg.data == 'close':
                                await ws.close()
                                break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                log.error('[daapd] Connection to forked-daapd websocket closed')
                self.connected = False
            except:
                log.error('[daapd] Failed to connect to forked-daapd websocket. Retry in 1 sec.')
                self.connected = False
                try:
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    log.info('[daapd] Connection retry canceled')
                    await self.client.close()
                    break

        log.error('[daapd] Notify loop closed')

    async def play(self, uri):
        log.debug('[daapd] Start playback for uri={}'.format(uri))
        async with self.client.post('{}/api/queue/items/add?uris={}&clear=true&shuffle=false&playback=start'.format(self.url, uri)) as resp:
            log.info('[daapd] Play request status={}'.format(resp.status))

    async def pause(self):
        log.debug('[daapd] Pause playback')
        async with self.client.put('{}/api/player/pause'.format(self.url)) as resp:
            log.info('[daapd] Pause request status={}'.format(resp.status))

    async def next(self):
        log.debug('[daapd] Play next track')
        async with self.client.put('{}/api/player/next'.format(self.url)) as resp:
            log.info('[daapd] Play next request status={}'.format(resp.status))

    async def previous(self):
        log.debug('[daapd] Play previous track')
        async with self.client.put('{}/api/player/previous'.format(self.url)) as resp:
            log.info('[daapd] Play previous request status={}'.format(resp.status))

    async def volume_up(self, vol_up):
        log.debug('[daapd] Volume up (+{})'.format(vol_up))
        async with self.client.put('{}/api/player/volume?step={}'.format(self.url, vol_up)) as resp:
            log.info('[daapd] Volume up request status={}'.format(resp.status))

    async def volume_down(self, vol_down):
        log.debug('[daapd] Volume down (-{})'.format(vol_down))
        async with self.client.put('{}/api/player/volume?step=-{}'.format(self.url, vol_down)) as resp:
            log.info('[daapd] Volume down request status={}'.format(resp.status))

