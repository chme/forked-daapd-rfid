
import asyncio
import aiohttp


class ForkedDaapd:

    def __init__(self, loop):
        self.loop = loop
        self.running = True

    async def notify_loop(self):
        async with aiohttp.ClientSession() as client:
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
