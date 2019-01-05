
import asyncio
import aiohttp


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
                    print('Connection established')
                    await ws.send_json({ 'notify': ['player', 'outputs', 'volume'] })
                    async for msg in ws:
                        print(msg.data)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if msg.data == 'close':
                                await ws.close()
                                break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                print('Connection closed')
            except:
                print('Connection failed')
                await asyncio.sleep(1)

        print('Notify loop closed')

    async def play(self, uri):
        async with self.client.post('{0}/api/queue/items/add?uris={1}&clear=true&shuffle=false&playback=start'.format(self.url, uri)) as resp:
            print('Play request: {0}'.format(resp.status))

    async def pause(self):
        async with self.client.put('{0}/api/player/pause'.format(self.url)) as resp:
            print('Pause request: {0}'.format(resp.status))
