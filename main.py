from picamera import PiCamera
import picamera
from time import sleep, time
import numpy as np
import datetime
import threading
BUFFERTIME = 10
camera = PiCamera()
camera.rotation = 180
camera.start_preview(alpha=200)
camera.resolution = (1920, 1080)
RECORDING_INTERVAL = 5
def getTime():
    return int(time())
def getFileName():
    t = getTime()
    lastT = t - t % RECORDING_INTERVAL
    return str(lastT) + ".h264"
def recordingFunc():
    global camera
    lastFile = None
    lastFileName = ""

    while (1 == 1):
        t = getTime()
        fname = getFileName()
        if fname != lastFileName:
            if lastFileName != "":
                camera.stop_recording()
            camera.start_recording(fname)
            lastFileName = fname
        sleep(1)


def write_video(stream, fname):
    print('Writing video!')
    with stream.lock:
        # Find the first header frame in the video
        for frame in stream.frames:
            if frame.frame_type == picamera.PiVideoFrameType.sps_header:
                stream.seek(frame.position)
                break
        # Write the rest of the stream to disk
        with open(fname, 'wb') as output:
            output.write(stream.read())
LISTLEN = 10
class MotionDetector:
    def __init__(self):
        self.threshold = 3000000
        self.thresholdSmall = 1000000
        self.seq = []
        self.status = "INIT"

    def different(self, pre, now):
        return np.sum(np.square(pre - now)) / 100.0
    def moving(self, v1, v2):
        l = v1 - v2
        if l > 0: 
            return l
        else:
            return -l
    def next(self, now, prev):
        # print prev, now
        diff = self.different(prev, now)
        print diff
        self.seq.append(diff)
        global LISTLEN
        if len(self.seq) > LISTLEN:
            self.seq.pop(0)
            if self.status == "INIT":
                self.status = "IDLE"

        if len(self.seq) == LISTLEN and self.status == "IDLE":
            cntLarge = 0
            cntSmall = 0
            for i in range(LISTLEN - 4, LISTLEN):
                # dist = self.moving(self.seq[i], self.seq[i + 1])
                dist = self.seq[i]
                if dist > self.threshold:
                    cntLarge += 1
                    cntSmall += 1
                elif (dist > self.thresholdSmall):
                    cntSmall += 1
            if (cntLarge * 3 + cntSmall >= 4):
                self.status = "MOVING"
            return False

        elif len(self.seq) == 10 and self.status == "MOVING":
            cntLarge = 0
            cntSmall = 0
            for i in range(LISTLEN - 4, LISTLEN):
                # dist = self.moving(self.seq[i], self.seq[i + 1])
                dist = self.seq[i]
                if dist > self.threshold:
                    cntLarge += 1
                    cntSmall += 1
                elif dist > self.thresholdSmall:
                    cntSmall += 1
            if (cntLarge == 0 and cntSmall < 2):
                self.status = "IDLE"
                return True
            else:
                return False
        
        

        return False



# recordingThread = threading.Thread(target=recordingFunc)
# recordingThread.daemon = True
# recordingThread.start()

reso = (1920,1088)




output = np.empty((1920 * 1088* 3), dtype=np.uint8) 
prev = np.empty((1920*1088*3), dtype=np.uint8)
stream = picamera.PiCameraCircularIO(camera, seconds=BUFFERTIME)
camera.start_recording(stream, format='h264')
md = MotionDetector()

try:
    while True:
        camera.wait_recording(0.3)
        camera.capture(output, 'rgb')
        write_now = md.next(output, prev)
        print prev, output
        temp = prev
        prev = output
        output = temp
        print md.status
        if write_now:
            # camera.wait_recording(10)
            write_video(stream, "test.h264")
finally:
    camera.stop_recording()


# camera.start_recording('test.h264')

# for i in range(10):
#     sleep(1)
#     camera.capture(output, 'rgb')
#     print different(output, prev)
#     temp = output
#     output = prev
#     prev = temp
# camera.stop_recording()

# fi = open("test.h264", "a")
# camera.start_recording(fi)
# for i in range(3):
#     sleep(1)
#     camera.capture(output, 'rgb')
#     print different(output, prev)
#     temp = output
#     output = prev
#     prev = temp
# camera.stop_recording()
camera.stop_preview()
