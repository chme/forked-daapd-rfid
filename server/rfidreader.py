
from mfrc522 import (
    SimpleMFRC522,
    StatusCode
)
import asyncio
import logging

from .pixels import Pixels, PixelType

log = logging.getLogger('main')

class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        log.debug('[rfid] Timout reached')
        await self._callback()

    def cancel(self):
        self._task.cancel()

class RfidReader:

    def __init__(self, loop, daapd, web_socket, neo_pixels):
        self.loop = loop
        self.daapd = daapd
        self.web_socket = web_socket
        self.neo_pixels = neo_pixels
        self.reader = SimpleMFRC522()

        self.current_tag_id = None
        self.current_tag_content = None

        self.current_task = None
        self.timer = None

    def start(self):
        log.debug('[rfid] Starting RFID reader ...')
        log.debug('[rfid] Wait for daapd connection established ...')
        self.loop.run_until_complete(self._wait_for_daapd())
        log.debug('[rfid] Init RFID reader ...')
        self.reader.init()
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

    async def _wait_for_daapd(self):
        if self.neo_pixels:
            self.neo_pixels.set_state(Pixels.YELLOW, PixelType.BLINK)
        
        while not self.daapd.connected:
            await asyncio.sleep(2)
    
    async def read_tags(self):
        try:
            log.debug('[rfid] Read task started. Wating for new tag to start playback')
            if self.neo_pixels:
                self.neo_pixels.set_state(Pixels.AZURE, PixelType.PULSE)
            self.current_task = self.loop.run_in_executor(None, self.reader.read_text)
            status, uid, text = await self.current_task

            if status == StatusCode.STATUS_CANCELED:
                log.debug('[rfid] Wating for tag read was canceled. Quit read task')
                self.__reset_current_tag()
                if self.neo_pixels:
                    self.neo_pixels.set_state(Pixels.YELLOW, PixelType.BLINK)
                await asyncio.sleep(1)
                return
            
            if status:
                self.current_tag_id = uid.to_num()
                self.current_tag_content = text
                log.info('[rfid] New tag found with id={0} and content={1}'.format(uid, text))
                asyncio.ensure_future(self.web_socket.send_current_tag(uid.to_num(), text))
                await self.daapd.play(text)
    
                log.debug('[rfid] Wating for tag removed to pause playback')
                if self.neo_pixels:
                    self.neo_pixels.set_state(Pixels.AZURE, PixelType.FIXED)
                self.current_task = self.loop.run_in_executor(None, self.reader.wait_for_card_removed)
                removed = await self.current_task
    
                if not removed:
                    log.debug('[rfid] Wating for tag removed was canceled. Quit read task')
                    if self.neo_pixels:
                        self.neo_pixels.set_state(Pixels.YELLOW, PixelType.BLINK)
                    await asyncio.sleep(1)
                    return
                
                log.info('[rfid] Tag with id={0} and content={1} removed'.format(self.current_tag_id, self.current_tag_content))
                self.__reset_current_tag()
                await self.daapd.pause()
            else:
                self.__reset_current_tag()
                if self.neo_pixels:
                    self.neo_pixels.set_colors(Pixels.RED, Pixels.RED, PixelType.BLINK, 1)
                log.error('[rfid] Error reading tag (status: {})'.format(status))

            await asyncio.sleep(1)
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
                if self.neo_pixels:
                    self.neo_pixels.set_state(Pixels.YELLOW, PixelType.BLINK)
                self.reader.cancel_wait()
                await asyncio.wait([self.current_task])
                log.debug('[rfid] Current rfid task completed. Coninue writing tag')

            log.info('[rfid] Waiting for tag to write new content={0}'.format(new_content))
            if self.neo_pixels:
                self.neo_pixels.set_state(Pixels.YELLOW, PixelType.PULSE)
            self.timer = Timer(30, self.reader.cancel_wait)
            self.current_task = self.loop.run_in_executor(None, self.reader.write_text, new_content)
            status, uid, __ = await self.current_task

            if status == StatusCode.STATUS_CANCELED:
                log.debug('[rfid] Wating for tag write was canceled. Quit read task')
                log.warning('[rfid] Reschedule read task after write task was canceled')
                if self.neo_pixels:
                    self.neo_pixels.set_colors(Pixels.RED, Pixels.RED, PixelType.BLINK, 1)
                await asyncio.sleep(1)
                asyncio.ensure_future(self.read_tags(), loop=self.loop)
                return
            
            self.timer.cancel()
            
            if status:
                if self.neo_pixels:
                    self.neo_pixels.set_state(Pixels.GREEN, PixelType.FIXED)
                asyncio.ensure_future(self.web_socket.send_message('WRITE_SUCCESS', 'Tag created successfully. Please remove tag to proceed.'))
            else:
                if self.neo_pixels:
                    self.neo_pixels.set_state(Pixels.RED, PixelType.FIXED)
                asyncio.ensure_future(self.web_socket.send_message('WRITE_ERROR', 'Failed to create tag. Please remove tag to retry.'))

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
