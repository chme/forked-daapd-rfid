
from MFRC522 import SimpleMFRC522
import asyncio
import aiohttp

class RfidReader:

    MODE_READ    = 1
    MODE_WRITE   = 2

    run = True

    tags = []

    def __init__(self, loop, conf):
        self.loop = loop
        self.mode = self.MODE_READ
        self.reader = SimpleMFRC522.SimpleMFRC522()
        self.forked_daapd_url = 'http://' + conf.get('forked-daapd', 'host') + ':' + conf.get('forked-daapd', 'port')
        self.next_tag = None

    def cancel(self):
        self.run = False
        self.reader.cancel_wait()

    def write_next_tag(self, content):
        print('Write next tag: ', content)
        self.next_tag = content
        self.mode = self.MODE_WRITE

    async def handle_tags(self):
        async with aiohttp.ClientSession() as client:
            try:
                while self.run:
                    await self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
                    uid, content = self.reader.read()
                    print('Tag found', uid, content)

                    if uid == None:
                        print('Failed to read tag id')
                        continue

                    if self.mode == self.MODE_READ:
                        await self.play(uid, content, client)
                    elif self.mode == self.MODE_WRITE:
                        self.write_tag(uid, content)
                    else:
                        print('ERR Unknown mode', self.mode)

                    await self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)

                    if self.mode == self.MODE_READ:
                        await self.pause(client)
                    elif self.mode == self.MODE_WRITE:
                        self.mode = self.MODE_READ
                    else:
                        print('ERR Unknown mode', self.mode)

            except asyncio.CancelledError:
                print('>>>> CancelledError')

    async def play(self, uid, content, client):
        print('PLAY', id, content)

        self.tags.append({ 'id' : id, 'content' : content })

        async with client.put(self.forked_daapd_url + '/api/queue/clear') as resp:
            print('clear: ', resp.status)
            assert resp.status < 300
            async with client.put(self.forked_daapd_url + '/api/player/shuffle?state=false') as resp:
                assert resp.status < 300
                async with client.post(self.forked_daapd_url + '/api/queue/items/add?uris=' + content) as resp:
                    assert resp.status < 300
                    async with client.put(self.forked_daapd_url + '/api/player/play') as resp:
                        assert resp.status < 300

    async def pause(self, client):
        print('PAUSE')

        async with client.put(self.forked_daapd_url + '/api/player/pause') as resp:
            print('clear: ', resp.status)
            assert resp.status < 300

    def write_tag(self, uid, content):
        print('WRITE TAG', uid, content)

        if (self.next_tag):
            self.reader.write_text(uid, self.next_tag)

        self.next_tag = None
