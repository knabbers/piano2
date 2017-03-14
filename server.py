import http.server
import tone
import math

generator = tone.ToneGenerator()

ADDRESS = ''
PORT = 8000


min_delta = 10000000
max_delta = -10000000
cnt = 0

allfreqs = [440.0 * 2**(k/12.0) for k in range(12*8)]

claps = dict()
strengths = []
import time

def size_to_delta(size=3):
	return float(size)/330
def round_note(toplay):
	return min(allfreqs, key=lambda x:abs(x-toplay))

class Handler(http.server.BaseHTTPRequestHandler):

	def do_GET(self):
		global min_delta
		global max_delta
		global timestamps
		global cnt
		#max_delta = size_to_delta(2)
		#min_delta = -max_delta

		(_, id, ts, vol) = self.path.split('/')
		id, ts, vol = int(id), float(ts), float(vol)
		id = 1
		claps[id] = (ts,vol)
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		event.set()


###########################
###########################
import threading
event = threading.Event()

import pygame
import time
import pygame.midi

pygame.midi.init()
player= pygame.midi.Output(0)
player.set_instrument(0,1)

def match():	
	global min_delta
	global max_delta
	global timestamps
	global cnt
	try:
		note_prev = None
		while True:
			event.wait()
			event.clear()
			if 0 in claps and 1 in claps:
				delta = (claps[0][0] - claps[1][0])
				strength = (math.sqrt(claps[0][1]) + math.sqrt(claps[1][1]))**2
				strengths.append(strength)
				if abs(delta) < size_to_delta(3):
					cnt += 1
					print ("delta: " + str(delta))
					if cnt <= 2:
						print ("calibrating!!!!!")
						min_delta = min(min_delta,delta)
						max_delta = max(max_delta,delta)
						print(min_delta)
						print(max_delta)				
					else:
						assert min_delta != max_delta
						rng = max_delta-min_delta
						#delta = min(delta,max_delta)
						#delta = max(delta,min_delta)
						if min_delta-rng/12 <= delta <= max_delta+rng/12:
							pos = (delta-min_delta)/(max_delta-min_delta)
							pos = min(pos, 1.0)
							pos = max(pos, 0.0)
							print ("Pos: " + str(pos))
							toplay = 2*880 * 2**(pos)

							# generator.play(int(round_note(toplay)), 0.1, 1)
							# while generator.is_playing():
							# 	pass                # Do something useful in here (e.g. recording)
							note = int(round(60+pos*12))
							if note_prev!=None:
								player.note_off(note_prev, 127, 1)

							velocity = 127
							# if len(strengths) >= 2:
							# 	mn = min(strengths)
							# 	mx = max(strengths)
							# 	if mn != mx:
							# 		velocity = int(round(127.0*(strength-mn)/(mx-mn) ))
							# 		print ("v: " + str(velocity))

							player.note_on(note, velocity,1)
							note_prev = note
						else:
							print ("not in range!")
	finally:
		print("Quitting pygame...")
		pygame.quit()


thr = threading.Thread(target=match)
thr.daemon = True
thr.start()


###########################
###########################
# clap captuing  thread
import threading
import _portaudio
import myslowclap as sc
_portaudio.initialize()
CLIENT_ID = 0

def clap_pusher():
	time.sleep(0.2)
	print("listening...")

	feed = sc.MicrophoneFeed()
	detector = sc.RateLimitedDetector(sc.AmplitudeDetector(feed, threshold=3000),0.1)

	start_time = None

	for clap in detector:
	    # do something
	    if start_time==None:
	    	start_time = clap.time #time.perf_counter()
	    	print ("Synced!")
	    else:
		    t = clap.time - start_time
		    print( str(t) + "  " + str(clap.volume) )
		    claps[CLIENT_ID] = (t,clap.volume)
		    event.set()
 
thr = threading.Thread(target=clap_pusher)
thr.daemon = True
thr.start()



###########################
###########################

httpd = http.server.HTTPServer((ADDRESS, PORT), Handler)

print("serving at port", PORT)
httpd.serve_forever()



