#!/usr/bin/python

import roslib;roslib.load_manifest('mrobot_bringup')  
import rospy
import serial
import time
from mrobot_bringup.msg import sr04
SERIAL_TIMEOUT = 2
TTY_NAME = "/dev/ttyACM0"
TTY_BAUDRATE = 115200

class ReadDistanceSensor(object):
    def __init__(self):
        self.ser = serial.Serial(TTY_NAME, baudrate=TTY_BAUDRATE, timeout=SERIAL_TIMEOUT)

    def read(self):
        #there will be ascii 13 10 in last two
        line = self.ser.readline()
        return line[:-2]

if __name__ == "__main__":
    print ('This is readDistanceSensor')
    read = ReadDistanceSensor()
    rospy.init_node('sr04_publisher', anonymous=True)
    pub = rospy.Publisher('sr04_distance', sr04, queue_size=10)

    while True:
        line = read.read()
        datas = line.split(",")
        if len(datas) == 4:
            sr = sr04()
            try:
                sr.front = int(datas[0])
                sr.left = int(datas[1])
                sr.right = int(datas[2])
                sr.back = int(datas[3])
                pub.publish(sr)
            except Exception, e:
                print e
        print "string = %s, time = %f" % (line, time.time())
        time.sleep(0.2)
