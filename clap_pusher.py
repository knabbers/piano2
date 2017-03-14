# Python 3, please
HOST = "192.168.0.22"
PORT = 8000
CLIENT_ID = 1

import _portaudio
_portaudio.initialize()

import threading
import myslowclap as sc
import urllib.request
import time

time.sleep(0.2)
print("listening...")

feed = sc.MicrophoneFeed()
detector = sc.RateLimitedDetector(sc.AmplitudeDetector(feed, threshold=4000),0.1)

start_time = None

def get_async(url):
	def get_url():
		t1 = time.perf_counter()
		urllib.request.urlopen(url).read()
		print ("latency (ms): " + str(int( (time.perf_counter() - t1)*1000)) )
	t = threading.Thread(target=get_url)
	t.daemon = True
	t.start()



for clap in detector:
    if start_time==None:
    	start_time = clap.time #time.perf_counter()
    	print ("Synced!")
    else:
	    t = clap.time - start_time
	    print( str(t) + "  " + str(clap.volume) )
	    get_async("http://" + HOST + ":" + str(PORT)+"/"+str(CLIENT_ID)+"/"+str(t))
	    









