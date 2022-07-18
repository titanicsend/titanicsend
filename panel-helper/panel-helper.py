#! /usr/bin/env python3

import asyncio
import os

from pyartnet import ArtNetNode
from time import sleep

DATAFILE = "data.txt"
LAST_LOADED = 0
PANELS = dict()
CHANNELS = dict()

async def check_datafile():
  global LAST_LOADED
  last_changed = os.path.getmtime(DATAFILE)
  if last_changed == LAST_LOADED:
    return
  assert last_changed > LAST_LOADED
  LAST_LOADED = last_changed
  PANELS.clear()
  CHANNELS.clear()
  controllers = dict()

  fd = open(DATAFILE, 'r')
  for line in fd.readlines():
    line = line.strip()
    tokens = line.split(" ")
    if "." in line:
      ip = tokens.pop(0)
      pairs = [t.split(":") for t in tokens]
      assert ip not in controllers
      controllers[ip] = pairs
    else:
      panel = tokens.pop(0)
      num_pixels = 0
      for token in tokens:
        if token.isnumeric():
          num_pixels += int(token)
        elif all(c == 'g' for c in token):
          num_pixels += len(token)
        else:
          raise Exception("bad panel: %r" % line)
      assert panel not in PANELS
      PANELS[panel] = dict(tokens=list(tokens), num_pixels=num_pixels)

  for ip in controllers:
    pairs = controllers[ip]
    node = ArtNetNode(ip)
    await node.start()
    for port, panel_id in pairs:
      num_pixels = PANELS[panel_id]["num_pixels"]
      print ("Panel %s has %r pixels" % (panel_id, num_pixels))
      universe = node.add_universe(int(port) * 10)
      channel  = universe.add_channel(start=1, width=3 * num_pixels)
      CHANNELS[channel] = panel_id
  print ("Loaded")


async def draw_pixels(anim_frame):
  for channel, panel_id in CHANNELS.items():
    panel = PANELS[panel_id]
    fade = []
    row_phase = 0
    for token in panel["tokens"]:
      if token.isnumeric():
        row_len = int(token)
        if row_phase == 0:
          rgb = [0,50,0]
          af = anim_frame
        else:
          rgb = [0,0,50]
          af = 9 - anim_frame
        for i in range(row_len):
          if i % 10 == af:
            fade.extend([50, 50, 50])
          else:
            fade.extend(rgb)
        row_phase = 1 - row_phase
      else:
        fade.extend([50,0,0] * len(token))
    channel.add_fade(fade, 0)
    #await channel.wait_till_fade_complete()

loop = asyncio.get_event_loop()
anim_frame = 0
while True:
  loop.run_until_complete(check_datafile())
  loop.run_until_complete(draw_pixels(anim_frame))
  anim_frame = (anim_frame + 1) % 10
  sleep(0.1)
