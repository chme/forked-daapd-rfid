
import asyncio
import aiohttp


class ForkedDaapd:

    def __init__(self, loop, conf):
        self.loop = loop
        self.client = self.loop.run_until_complete(aiohttp.ClientSession())

    async def notify_loop(self):
        async with session.ws_connect('http://example.org/ws') as ws:
            await ws.send_str('data')
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close':
                        await ws.close()
                        break
                    else:
                        await ws.send_str(msg.data + '/answer')
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
