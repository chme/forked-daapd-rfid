
from MFRC522 import SimpleMFRC522
import asyncio
import aiohttp
import logging

log = logging.getLogger('main')

class RfidReader:

    def __init__(self, loop, daapd, web_socket):
        self.loop = loop
        self.daapd = daapd
        self.web_socket = web_socket
        self.reader = SimpleMFRC522.SimpleMFRC522()

        self.current_tag_id = None
        self.current_tag_content = None

        self.current_task = None

    def __reset_current_tag(self):
        self.current_tag_id = None
        self.current_tag_content = None
        asyncio.ensure_future(self.web_socket.send_current_tag(self.current_tag_id, self.current_tag_content))

    def current_tag(self):
        return self.current_tag_id, self.current_tag_content

    async def read_tags(self):
        try:
            log.debug('[rfid] Read task started. Wating for new tag to start playback')
            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
            await self.current_task

            self.current_tag_id, self.current_tag_content = self.reader.read()
            log.info('[rfid] New tag found with id={0} and content={1}'.format(self.current_tag_id, self.current_tag_content))
            asyncio.ensure_future(self.web_socket.send_current_tag(self.current_tag_id, self.current_tag_content))
            await self.daapd.play(self.current_tag_content)

            log.debug('[rfid] Wating for tag removed to pause playback')
            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)
            await self.current_task

            log.info('[rfid] Tag with id={0} and content={1} removed'.format(self.current_tag_id, self.current_tag_content))
            self.__reset_current_tag()
            await self.daapd.pause()

            log.debug('[rfid] Reschedule read task')
            asyncio.ensure_future(self.read_tags(), loop=self.loop)

        except asyncio.CancelledError:
            log.info('[rfid] Read task canceled')
            self.reader.cancel_wait()

    async def write_tag(self, new_content):
        try:
            log.debug('[rfid] Write task started')
            if self.current_task:
                log.debug('[rfid] Cancel current rfid task')
                self.current_task.cancel()
                asyncio.wait(self.current_task)
                log.debug('[rfid] Current rfid task completed. Coninue writing tag')

            log.info('[rfid] Waiting for tag to write new content={0}'.format(new_content))
            self.current_task =  self.loop.run_in_executor(None, self.reader.wait_for_tag_available)
            await self.current_task

            uid, content = self.reader.read()
            log.info('[rfid] Tag found with id={0} and content={1}'.format(uid, content))
            self.reader.write_text(uid, new_content)
            asyncio.ensure_future(self.web_socket.send_message('WRITE_SUCCESS', 'Tag created successfully. Please remove tag to proceed.'))

            log.info('[rfid] Tag written. Waiting for tag removed')
            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_tag_removed)
            await self.current_task
            log.info('[rfid] Tag with id={0} removed'.format(uid))
            self.__reset_current_tag()

            log.debug('[rfid] Reschedule read task after write')
            asyncio.ensure_future(self.read_tags(), loop=self.loop)

        except asyncio.CancelledError:
            log.warning('[rfid] Write task canceled')
            self.reader.cancel_wait()

            log.warning('[rfid] Reschedule read task after write task was canceled')
            asyncio.ensure_future(self.read_tags(), loop=self.loop)
