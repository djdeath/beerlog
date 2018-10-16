# pylint: disable=missing-docstring

from __future__ import print_function

from PIL import ImageFont
from luma.core.render import canvas as LumaCanvas

from errors import BeerLogError


class LumaDisplay(object):

  MENU_ITEMS = ['un', 'deux', 'trois', 'douze']

  MENU_TEXT_X = 2
  MENU_TEXT_HEIGHT = 10

  def __init__(self, events_queue=None):
    self._events_queue = events_queue
    self.luma_device = None
    self._menu_index = 0
    self._text_font = ImageFont.load_default()

    if not self._events_queue:
      raise BeerLogError('Display needs an events_queue')

  def Setup(self):
    is_rpi = False
    try:
      with open('/sys/firmware/devicetree/base/model', 'r') as model:
        is_rpi = model.read().startswith('Raspberry Pi')
    except IOError:
      pass

    if is_rpi:
      from gui import sh1106
      device = sh1106.WaveShareOLEDHat(queue=self._events_queue)
    else:
      print('Is not a RPI, running PyGame')
      from gui import emulator
      device = emulator.Emulator(queue=self._events_queue)

    device.Setup()
    device.Loop()
    self.luma_device = device.GetDevice()

  def _DrawMenuItem(self, drawer, number):
    selected = self._menu_index == number
    rectangle_geometry = (
        self.MENU_TEXT_X,
        number * self.MENU_TEXT_HEIGHT,
        self.luma_device.width,
        ((number+1) * self.MENU_TEXT_HEIGHT)
        )
    text_geometry = (
        self.MENU_TEXT_X,
        number*self.MENU_TEXT_HEIGHT
        )
    if selected:
      drawer.rectangle(
          rectangle_geometry, outline='white', fill='white')
      drawer.text(
          text_geometry,
          self.MENU_ITEMS[number],
          font=self._text_font, fill='black'
          )
    else:
      drawer.text(
          text_geometry,
          self.MENU_ITEMS[number],
          font=self._text_font, fill='white')

  def DrawMenu(self):
    with LumaCanvas(self.luma_device) as drawer:
      drawer.rectangle(
          self.luma_device.bounding_box, outline="white", fill="black")
      for i in range(len(self.MENU_ITEMS)):
        self._DrawMenuItem(drawer, i)

  def DrawWho(self, who):
    with LumaCanvas(self.luma_device) as drawer:
      drawer.text((0, 0), who, font=self._text_font, fill="white")

  def MenuDown(self):
    self._menu_index = ((self._menu_index + 1)%len(self.MENU_ITEMS))
    self.DrawMenu()

  def MenuUp(self):
    self._menu_index = ((self._menu_index - 1)%len(self.MENU_ITEMS))
    self.DrawMenu()

  def MenuRight(self):
    pass


# vim: tabstop=2 shiftwidth=2 expandtab
