#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist
import sys, select, termios, tty
import time
from evdev import InputDevice
from select import select

def detectInputKey():
    dev = InputDevice('/dev/input/event1')
    while True:
        select([dev], [], [])
        for event in dev.read():
            dealKeyEvent(event.code, event.value)
            #print "code:%s value:%s" % (event.code, event.value)

def dealKeyEvent(key, value):
    x = 0
    th = 0
    
    print "dealKeyEvent key:%s value:%s" % (key, value)

    if (key != 72 and key != 80 and key != 75 and key != 77):
        return

    if (value == 0):
        twist = Twist()
        twist.linear.x = x; twist.linear.y = 0; twist.linear.z = 0
        twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = th
        pub.publish(twist)
        return

    if (key == 72): #front
        print "front"
        x = 0.3
    elif (key == 80): #back
        x = -0.3
    elif (key == 75):
        th = 0.3
    elif (key == 77):
        th = -0.3

    twist = Twist()
    twist.linear.x = x; twist.linear.y = 0; twist.linear.z = 0
    twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = th
    pub.publish(twist)


if __name__ == '__main__':
    rospy.init_node('turtlebot_teleop')
    pub = rospy.Publisher('cmd_vel', Twist, queue_size=5)
    detectInputKey()

