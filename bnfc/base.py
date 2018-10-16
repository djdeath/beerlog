"""BeerLog main script"""

from __future__ import print_function

import binascii
import logging
import multiprocessing
import time

import nfc

from errors import BeerLogError
from gui import constants
from gui.base import BaseEvent


class NFCEvent(BaseEvent):
  """Event for a NFC tag."""

  def __init__(self, uid=None):
    super(NFCEvent, self).__init__(constants.EVENTTYPES.NFCSCANNED)
    self.uid = uid

  def __str__(self):
    return 'NFCEvent uid:{0:s} [{1!s}]'.format(self.uid, self.timestamp )


class NFC215(object):
  """Handles read operations on NFC215 tags."""
  BULK_READ_PAGE_COUNT = 4
  PAGE_SIZE = 4
  TAG_FILE_SIZE = 532

  @staticmethod
  def ReadUIDFromTag(tag):
    """Reads UID from a tag.

    Args:
      tag(nfc.tag.tt2_nxp.NTAG215): the input data read from the tag.
    Returns:
      uid(str): the tag uid in form 0x0580000000050002.
    """
    uid = None
    if tag.product == 'NXP NTAG215':
      bytes_array = tag.read(21)[0:8]
      uid = '0x{0}'.format(binascii.hexlify(bytes_array))
    else:
      logging.debug('Unknown tag product: {0:s}'.format(tag.product))
    return uid

  @staticmethod
  def ReadAllPages(tag):
    """Displays all pages from tag

    Args:
      tag(nfc.tag.tt2_nxp.NTAG215): the input data read from the tag.
    """
    pages = []
    for i in range(0, (NFC215.TAG_FILE_SIZE/NFC215.PAGE_SIZE), 4):
      page = tag.read(i)
      print('{0!s}:{1!s}'.format(i, binascii.hexlify(page).upper()))
      pages.append(binascii.hexlify(page).upper())
    print(''.join(pages))


class BeerNFC(object):
  """BeerNFC class.

  Attributes:
    args(argparse.NameSpace): Parsed arguments.
    clf(nfc.clf.ContactlessFrontend): the NFC Frontend.
  """

  SCAN_TIMEOUT_MS = 3*1000 # 3sec

  def __init__(self, events_queue=None, should_beep=False):
    """Initializes a BeerNFS object.

    Args:
      events_queue(Queue.Queue): the common events queue.
      should_beep(bool): whether to beep when a tag is scanned.

    Raises:
      BeerLogError: if arguments are invalid.
    """
    self._events_queue = events_queue
    self._should_beep = should_beep

    if not self._events_queue:
      raise BeerLogError('Need an events queue')

    self._last_event = None
    self.process = None
#    self._last_taken_picture = None
#    self._picture_dir = None

  def OpenNFC(self, path=None):
    """Initializes the NFC reader.

    Args:
      path(str): the option path to the device.

    Raises:
      BeerLogError: when we couldn't open the device.
    """
    self.process = multiprocessing.Process(target=self._DoNFC, args=(path,))

  def _DoNFC(self, path):
    """TODO"""
    try:
      with nfc.ContactlessFrontend(path) as clf:
        while True:
          success = clf.connect(
            rdwr={'on-connect': self.ReadTag}
          )

          if not success:
            logging.debug('Could not read NFC tag, or we timedout')
          time.sleep(0.1)
    except IOError as e:
      raise BeerLogError(
        (
          'Could not load NFC reader (path: {0}) with error: {1!s}\n'
          'Try removing some modules (hint: rmmod pn533_usb ; rmmod pn533'
          '; rmmod nfc'
        ).format(path, e))

  def _AddToQueue(self, event):
    """TODO"""
    if event:
      if self._last_event:
        delta = event.timestamp - self._last_event.timestamp
        delta_ms = delta.total_seconds() * 1000
        if delta_ms > self.SCAN_TIMEOUT_MS:
          self._events_queue.put(event)
        else:
          logging.debug('Already scanned {0!s} recently'.format(event))
      else:
        self._events_queue.put(event)
      self._last_event = event

  def ReadTag(self, tag):
    """Reads a tag from the NFC reader.

    Args:
      tag(nfc.tag): the tag object to read.

    Returns:
      bytearray: True if the read operation was successful,
        or None if it wasn't.
    """
    if isinstance(tag, nfc.tag.tt2.Type2Tag):
      uid = NFC215.ReadUIDFromTag(tag)
      if uid:
        event = NFCEvent(uid=uid)
        self._AddToQueue(event)
      return self._should_beep
    return False

# vim: tabstop=2 shiftwidth=2 expandtab