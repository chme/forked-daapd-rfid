
import asyncio
import aiohttp


class ForkedDaapd:

    def __init__(self, loop):
        self.loop = loop
        self.running = True
        self.client = aiohttp.ClientSession()

    async def notify_loop(self):
        async with self.client as client:
            while self.running:
                try:
                    async with client.ws_connect('http://localhost:3688', protocols=('notify',)) as ws:
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

            print('Session closed')

    async def play(self, uri):
        async with self.client as client:
            async with client.put('http://localhost:3689' + '/api/queue/clear') as resp:
                assert resp.status < 300
                async with client.put('http://localhost:3689' + '/api/player/shuffle?state=false') as resp:
                    assert resp.status < 300
                    async with client.post('http://localhost:3689' + '/api/queue/items/add?uris=' + content) as resp:
                        assert resp.status < 300
                        async with client.put('http://localhost:3689' + '/api/player/play') as resp:
                            assert resp.status < 300

    async def pause(self):
        async with self.client as client:
            async with client.put('http://localhost:3689' + '/api/player/pause') as resp:
                assert resp.status < 300
