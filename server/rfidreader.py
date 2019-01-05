
from MFRC522 import SimpleMFRC522
import asyncio
import aiohttp

class RfidReader:

    def __init__(self, loop, conf):
        self.loop = loop
        self.reader = SimpleMFRC522.SimpleMFRC522()
        self.forked_daapd_url = 'http://' + conf.get('forked-daapd', 'host') + ':' + conf.get('forked-daapd', 'port')
        self.current_tag_id = None
        self.current_tag_content = None
        self.current_task = None

    def cancel(self):
        self.reader.cancel_wait()

    async def read_tags(self):
        try:
            print('Read tag')
            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
            await self.current_task

            self.current_tag_id, self.current_tag_content = self.reader.read()
            print('  Read tag : {0}'.format(self.current_tag_content))
            # TODO await self.play(uid, content, client)

            await self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)
            print('  Read tag : removed')
            self.current_tag_id = None
            self.current_tag_content = None

            # Reschedule task
            asyncio.ensure_future(self.read_tags(), loop=self.loop)
        except asyncio.CancelledError:
            print('Cancel read') # TODO
            self.reader.cancel_wait()

    async def write_tag(self, content):
        try:
            print('Write tag')
            if self.current_task:
                self.current_task.cancel()

            await self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
            uid, content = self.reader.read()
            print('  Write tag : start')
            self.reader.write_text(uid, content)
            print('  Write tag : written')

            await self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)
            print('  Write tag : removed')
            self.current_tag_id = None
            self.current_tag_content = None

            # Reschedule task
            asyncio.ensure_future(self.read_tags(), loop=self.loop)
        except asyncio.CancelledError:
            print('Cancel write') # TODO
            self.reader.cancel_wait()
