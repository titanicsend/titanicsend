#! /usr/bin/env python3

# Virtual pixels, consuming sACN 
# Pass a universe number and traffic on that universe will be displayed in your terminal.

import sacn
import sys
import time

from x256 import x256

FRAMERATE = 5

if len(sys.argv) != 2:
  raise Exception("Need a universe number")

universe=int(sys.argv[1])

receiver = sacn.sACNreceiver()
receiver.start()  # start the receiving thread

# Take an RGB value and return an ANSI escape sequence to show it in the terminal
def color(rgb):
  if rgb is None:
    return ""
  ix = x256.from_rgb(*rgb)
  return "\033[38;5;%dm" % ix

next_draw = 0
@receiver.listen_on('universe', universe=universe)
def show_pixels(packet):
  global next_draw
  now = time.time()
  if now < next_draw:
    return
  next_draw = now + 1.0 / FRAMERATE
  counts = []
  rgbs = []
  accum = []
  for n in packet.dmxData:
    accum.append(n)
    if len(accum) == 3:
      if rgbs and accum == rgbs[-1]:
        counts[-1] += 1
      else:
        rgbs.append(accum)
        counts.append(1)
      accum = []
  s = "\033[H\033[2J\033[0m"  # Clear screen and reset text color
  s += "%d: " % universe
  for rgb in rgbs:
    count = counts.pop(0)
    s += color(rgb)
    if count <= 4:
      s += "*" * count;
    else:
      s += "[%d]" % count;
  print (s)

# receiver.join_multicast(1)

while True:
  time.sleep(1)
