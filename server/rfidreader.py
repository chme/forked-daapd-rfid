
from MFRC522 import SimpleMFRC522
import asyncio
import aiohttp

class RfidReader:

    def __init__(self, loop, daapd):
        self.loop = loop
        self.daapd = daapd
        self.reader = SimpleMFRC522.SimpleMFRC522()
        self.current_tag_id = None
        self.current_tag_content = None
        self.current_task = None

    async def read_tags(self):
        try:
            print('Read tag')
            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
            await self.current_task

            self.current_tag_id, self.current_tag_content = self.reader.read()
            print('  Read tag : ##{0}##'.format(self.current_tag_content))
            await self.daapd.play(self.current_tag_content)

            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)
            await self.current_task
            print('  Read tag : removed')

            self.current_tag_id = None
            self.current_tag_content = None
            await self.daapd.pause()

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

            self.current_task =  self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
            await self.current_task
            uid, content = self.reader.read()
            print('  Write tag : start')
            self.reader.write_text(uid, content)
            print('  Write tag : written')

            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)
            await self.current_task
            print('  Write tag : removed')
            self.current_tag_id = None
            self.current_tag_content = None

            # Reschedule task
            asyncio.ensure_future(self.read_tags(), loop=self.loop)
        except asyncio.CancelledError:
            print('Cancel write') # TODO
            self.reader.cancel_wait()
            asyncio.ensure_future(self.read_tags(), loop=self.loop)
