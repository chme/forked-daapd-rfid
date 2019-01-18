
from MFRC522 import simple_mfrc522
import asyncio
import logging

log = logging.getLogger('main')

class RfidReader:

    def __init__(self, loop, daapd, web_socket):
        self.loop = loop
        self.daapd = daapd
        self.web_socket = web_socket
        self.reader = simple_mfrc522.SimpleMFRC522()

        self.current_tag_id = None
        self.current_tag_content = None

        self.current_task = None

    def start(self):
        log.debug('[rfid] Starting RFID reader ...')
        self.reader.init()
        log.debug('[rfid] Reschedule read task')
        asyncio.ensure_future(self.read_tags(), loop=self.loop)
        log.debug('[rfid] Starting RFID reader complete')

    def cleanup(self):
        log.debug('[rfid] RFID reader cleanup ...')
        self.reader.cleanup()
        log.debug('[rfid] RFID reader cleanup complete')

    def __reset_current_tag(self):
        self.current_tag_id = None
        self.current_tag_content = None
        asyncio.ensure_future(self.web_socket.send_current_tag(self.current_tag_id, self.current_tag_content))

    def current_tag(self):
        return self.current_tag_id, self.current_tag_content

    async def read_tags(self):
        try:
            log.debug('[rfid] Read task started. Wating for new tag to start playback')
            self.current_task = self.loop.run_in_executor(None, self.reader.read_text)
            status, uid, text = await self.current_task

            if status:
                self.current_tag_id = uid.to_num()
                self.current_tag_content = text
                log.info('[rfid] New tag found with id={0} and content={1}'.format(uid, text))
                asyncio.ensure_future(self.web_socket.send_current_tag(uid.to_num(), text))
                await self.daapd.play(text)
    
                log.debug('[rfid] Wating for tag removed to pause playback')
                self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_card_removed)
                removed = await self.current_task
    
                if not removed:
                    log.debug('[rfid] Wating for tag removed was canceled. Quit read task')
                    return
                
                log.info('[rfid] Tag with id={0} and content={1} removed'.format(self.current_tag_id, self.current_tag_content))
                self.__reset_current_tag()
                await self.daapd.pause()
            else:
                self.__reset_current_tag()
                log.error('[rfid] Error reading tag (status: {})'.format(status))

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
                await asyncio.wait([self.current_task])
                log.debug('[rfid] Current rfid task completed. Coninue writing tag')

            log.info('[rfid] Waiting for tag to write new content={0}'.format(new_content))
            self.current_task = self.loop.run_in_executor(None, self.reader.write_text(new_content))
            status, uid, __ = await self.current_task

            if status:
                asyncio.ensure_future(self.web_socket.send_message('WRITE_SUCCESS', 'Tag created successfully. Please remove tag to proceed.'))

            log.info('[rfid] Tag written. Waiting for tag removed')
            self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_card_removed)
            await self.current_task
            log.info('[rfid] Tag with id={} removed'.format(uid))

            log.debug('[rfid] Reschedule read task after write')
            asyncio.ensure_future(self.read_tags(), loop=self.loop)

        except asyncio.CancelledError:
            log.warning('[rfid] Write task canceled')
            self.reader.cancel_wait()

            log.warning('[rfid] Reschedule read task after write task was canceled')
            asyncio.ensure_future(self.read_tags(), loop=self.loop)
