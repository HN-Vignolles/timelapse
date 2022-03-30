#!/usr/bin/python3

import time
import subprocess
import signal
import sys
import glob
import os
import getopt
from pathlib import Path
from typing import final

# TODO: udev rule for matching /dev/camera
inputVideo = "/dev/video2"
framesPath = "./frames/"
diffPath = "./diff/"
n = 1


def sighandler(sig, frame):
    signal.signal(sig, signal.SIG_IGN)
    # kill the process group:
    os.kill(0, sig)
    print("Bye!")
    raise KeyboardInterrupt

def compile():
    args = ["/usr/bin/ffmpeg", "-hide_banner", "-loglevel", "warning"]
    args += ["-framerate","60","-i",framesPath + "%08d.jpg","-c:v","libx264","output.mp4"]
    print("\x1b[32;1m[ffmpeg]\x1b[0m Compiling with args: %s" % " ".join(args))
    subprocess.run(args)
    args = ["/usr/bin/ffmpeg", "-hide_banner", "-loglevel", "warning"]
    args += ["-framerate","60","-i",diffPath + "diff%08d.jpg","-c:v","libx264","diff.mp4"]
    print("\x1b[32;1m[ffmpeg]\x1b[0m Compiling diff with args: %s" % " ".join(args))
    subprocess.run(args)
    sys.exit(0)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c", ["compile"])
    except getopt.GetoptError as err:
        print(err)
        raise Exception()
    for o,a in opts:
        if o in ("-c","--compile"):
            compile()

    try:
        # TODO: use histogram to adjust exposure
        # Adjusting the webcam (I had to do this on my particular setup, try the defaults first):
        args = ["/usr/bin/v4l2-ctl","-d",inputVideo]
        args += ["-c", "power_line_frequency=1"]  # set to 50hz
        args += ["-c", "sharpness=100"]
        args += ["-c", "exposure_auto=1"]
        args += ["-c", "exposure_absolute=7"]  # Now I can _actually_ see
        subprocess.run(args)
    except Exception:
        print("\x1b[33;1m[v4l2-ctl]\x1b[0m \x1b[33munable to adjust camera controls\x1b[0m")
    else:
        print("\x1b[32;1m[v4l2-ctl]\x1b[0m successfully changed camera controls")

    Path(framesPath).mkdir(exist_ok=True)
    Path(diffPath).mkdir(exist_ok=True)
    frames = glob.glob(framesPath + "????????.jpg")
    if(len(frames) == 0):
        print("\x1b[33mno .jpg frames found\x1b[0m")
        n = 1
    else:
        n = max([int(a[len(framesPath):-4]) for a in frames]) + 1
    if n < 1:
        raise Exception("Count value error. It should be > 1")

    while True:
        count = "%08d" % n
        print("\x1b[32;1m[loop]\x1b[0m count: %s" % count)
        
        args = ["/usr/bin/ffmpeg", "-hide_banner", "-loglevel", "warning"]
        args += ["-i", inputVideo, "-frames:v", "1", framesPath + count + ".jpg"]
        result = subprocess.run(args, text=True, check=True, capture_output=True)
        # The warning "deprecated pixel format.." can be ignored.
        print("\x1b[32;1m[ffmpeg]\x1b[0m \x1b[33m%s\x1b[0m" % result.stderr)

        if n > 1:
            args = ["/usr/bin/compare", "-lowlight-color", "transparent", "-fuzz", "15%"]
            prev = "%08d" % (n - 1)
            args += [framesPath + prev + ".jpg", framesPath + count + ".jpg", diffPath + "diff" + count + ".jpg" ]
            result = subprocess.run(args,text=True, capture_output=True)
            print("\x1b[32;1m[compare]\x1b[0m \x1b[33mdiff frames: %s\x1b[0m" % ("True" if result.returncode else "False"))

        try:
            subprocess.run(["/usr/bin/xdg-screensaver", "reset"])
            subprocess.run(["/usr/bin/yad", "--fullscreen", "--timeout",
                       "10", "--image", "./frames/" + count + ".jpg"])

        except Exception:
            # nothing important
            ...
        
        time.sleep(60)  # 400
        n += 1


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGQUIT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)
    try:
        res = main()
    except subprocess.CalledProcessError as error:
        print(error)
        sys.stderr.write("\x1b[31;1m[subprocess]\x1b[0m \x1b[31m%s\x1b[0m\n" % error.stderr)
        res = error.returncode
    except Exception as error:
        sys.stderr.write(str(error))
        res = 1
    except KeyboardInterrupt:
        res = 0

    sys.exit(res)
