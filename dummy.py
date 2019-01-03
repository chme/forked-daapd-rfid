
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


loop = asyncio.get_event_loop()
forked_daapd = ForkedDaapd(loop)

try:
    print("(Press CTRL+C to quit)")
    asyncio.ensure_future(forked_daapd.notify_loop(), loop=loop)
    loop.run_forever()
except (KeyboardInterrupt):
    pass
