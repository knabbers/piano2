#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  detect_claps.py
#  clapper
#

"""
Detect claps using the microphone.
"""

from __future__ import absolute_import, print_function, division

import sys
import optparse
from collections import deque, namedtuple
import subprocess

import pyaudio
import numpy as np

CHUNK = 102
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
THRESHOLD = 1.5e7

Chunk = namedtuple('Chunk', 'data time')
Clap = namedtuple('Clap', 'time volume')

amp_sum = 0
amp_n = 0

class AmplitudeDetector():
    "Call a sufficiently noisy event a clap."

    def __init__(self, feed, threshold=THRESHOLD):
        self.feed = feed
        self.threshold = threshold

    def __iter__(self):
        for c in self.feed:
            r = self.detect(c)
            if r != None:
                dt,vol = r
                yield Clap(float(c.time+dt)/RATE, vol)

    def detect(self, chunk):
        # global amp_sum
        # global amp_n
        # amp_sum += abs(chunk.data).sum()
        # amp_n += 1
        # if amp_n % 100000000000 == 0:
        #     print("Mean: " + str(float(amp_sum)/float(amp_n)))
        # if abs(chunk.data).sum() > self.threshold:
        #     #print(abs(chunk.data).sum())
        #     return True

        overs = np.where(abs(chunk.data) > self.threshold)
        if len(overs[0]) > 0:
            dt = overs[0][0]
            vol = abs(chunk.data[dt])
            return (dt,vol)
        else:
            return None

class MicrophoneFeed(object):
    def __init__(self):
        self.enabled = True
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                  input=True, frames_per_buffer=CHUNK)
        self.t = 0 # in samples, not seconds

    def __iter__(self):
        while self.enabled:
            data = self.stream.read(CHUNK)
            chunk = np.fromstring(data, 'int16')
            yield Chunk(chunk, self.t)
            self.t += CHUNK

    def close(self):
        self.enabled = False



class RateLimitedDetector(AmplitudeDetector):
    def __init__(self, d, rate_limit=1):
        self.child = d
        self.last_clap = -rate_limit
        self.rate_limit = rate_limit

    def __iter__(self):
        for clap in self.child:
            if clap.time - self.last_clap > self.rate_limit:
                self.last_clap = clap.time
                yield clap


