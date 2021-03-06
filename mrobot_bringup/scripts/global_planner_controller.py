#!/usr/bin/python

#  uint8 PENDING=0
#  uint8 ACTIVE=1
#  uint8 PREEMPTED=2
#  uint8 SUCCEEDED=3
#  uint8 ABORTED=4
#  uint8 REJECTED=5
#  uint8 PREEMPTING=6
#  uint8 RECALLING=7
#  uint8 RECALLED=8
#  uint8 LOST=9

import roslib;roslib.load_manifest('mrobot_bringup')  
import rospy
import time
import geometry_msgs.msg
import move_base_msgs.msg
from std_srvs.srv import Empty
from std_msgs.msg import String
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped
from geometry_msgs.msg import PoseStamped
from actionlib_msgs.msg import GoalStatusArray
from actionlib_msgs.msg import GoalID
from move_base_msgs.msg import MoveBaseActionFeedback
from move_base_msgs.msg import MoveBaseActionResult
import copy


class MyGoal:
    def setGoal(self, id, goal):
        self.id = id
        self.goal = goal

    def isMatch(self, id):
        if (id == self.id):
            return true
        return false
    def getGoal(self):
        return self.goal


class MoveController(object):
    def __init__(self):
        self.startNavigation = False
        self.goalList = []
        self.isRobotStopped = True
        self.robotStoppedTime = 0
        self.cancelPub = rospy.Publisher('/move_base/cancel', GoalID, queue_size=2)
        self.goalPub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=2)
        self.initPosition = rospy.Publisher("initialpose", PoseWithCovarianceStamped, queue_size=2)            
        rospy.loginfo("wait for clear_costmaps service")
        rospy.wait_for_service('/move_base/clear_costmaps')
        self.clearMapService = rospy.ServiceProxy('/move_base/clear_costmaps', Empty)   
        rospy.loginfo("clear_costmaps service found!")   

    def initPositionMethod(self):
        init = PoseWithCovarianceStamped()
        init.header.seq = 10
        #init.header.stamp = rospy.Time.now()
        init.header.frame_id = "map"
        init.pose.covariance[0*6+0] = 0.25 #0.5*0.5
        init.pose.covariance[6*1+1] = 0.25
        init.pose.covariance[6*5+5] = 0.068538919452 #pi / 12 * pi / 12
        init.pose.pose.position.x = 20.420918
        init.pose.pose.position.y = 8.501009
        init.pose.pose.position.z = 0.000000
        init.pose.pose.orientation.x = 0.0
        init.pose.pose.orientation.y = 0.0
        init.pose.pose.orientation.z = 0.829574
        init.pose.pose.orientation.w = 0.558396
        self.initPosition.publish(init)

    def startMove(self, goal):
        self.startNavigation = True
        self.goalList.append(goal)
        self.resetRobotMoveParams() 
        rospy.loginfo("startMove, goallist size = %d", len(self.goalList))

    def stopMove(self, id):
        #if (self.goal.status.goal_id.id == result.status.goal_id.id):
        #newList = []
        #for i in self.goalList:
        #    if (i.header.frame_id != id):
        #        newList.append(i)
        #self.goalList = newList
        if (len(self.goalList) > 0):
            del self.goalList[0]        

        if (len(self.goalList) == 0):
            self.startNavigation = False
            self.resetRobotMoveParams()
        rospy.loginfo("stopMove, goalList size = %d", len(self.goalList))
        #else:
        #    rospy.loginfo("stopMove but id incorrect")

    def judgeGoalbalPathVaidateEffective(self, msg):
        if (self.startNavigation == True and self.isRobotStoppedMethod(msg) == True):
            if (self.isRobotStopped == True):
                stopDuration = time.time() - self.robotStoppedTime
                rospy.loginfo("robot has stopped %f second"%(stopDuration))
                if (stopDuration > 5.0):
                    self.restartGoal()
            else:
                self.isRobotStopped = True
                self.robotStoppedTime = time.time()
                rospy.loginfo("robot stopped")
        else:
            self.resetRobotMoveParams()
                
            
        
    def isRobotStoppedMethod(self, msg):
        if (msg.linear.x == 0 and msg.linear.y == 0 and msg.linear.z == 0):
            #rospy.loginfo("robot is stopped")
            return True
        return False

    def restartGoal(self):
        rospy.loginfo("MoveController restart goal")
        oldGoal = self.goalList[-1]
        #self.stopMove(None)
        #self.cancelPub.publish(GoalID())
        #time.sleep(1)
        newGoal = copy.copy(oldGoal)
        newGoal.header.stamp = rospy.Time.now()
        newGoal.header.seq += 1
        self.goalPub.publish(newGoal)

    def cancelHjmGoal(self):
        rospy.loginfo("MoveController cancel goal")
        self.cancelPub.publish(GoalID())     

    def clearCostmap(self):
        rospy.loginfo("MoveController clearCostmap")
        self.clearMapService()

    def resetRobotMoveParams(self):
        self.isRobotStopped = False
        self.robotStoppedTime = 0

def cmdVelcallback(msg):
    global moveController

    moveController.judgeGoalbalPathVaidateEffective(msg)
    #rospy.loginfo("cmdVelcallback Linear Components: [%f, %f, %f]"%(msg.linear.x, msg.linear.y, msg.linear.z))
    #rospy.loginfo("cmdVelcallback Angular Components: [%f, %f, %f]"%(msg.angular.x, msg.angular.y, msg.angular.z))


def goalCallback(moveBaseGoal):
    global moveController

    position = moveBaseGoal.pose.position
    orientation = moveBaseGoal.pose.orientation

    moveController.startMove(moveBaseGoal)

    rospy.loginfo("goalCallback id = %s, position [%f, %f, %f]"%(moveBaseGoal.header.frame_id, position.x, position.y, position.z))
    rospy.loginfo("goalCallback orientation [%f, %f, %f]"%(orientation.x, orientation.y, orientation.z))

def resultCallback(result):
    global moveController

    moveController.stopMove(id)

    rospy.loginfo("resultCallBack id = %s, status = %8u"%(result.status.goal_id.id, result.status.status))

def statusCallback(status):
    rospy.loginfo("statusCallback id = %s, status = %8u"%(status.status_list[0].goal_id.id, status.status_list[0].status))

def cancelCallback(cancel):
    rospy.loginfo("cancelCallback id = %s"%(cancel.id))

def currentGoalCallback(currentGoal):
    position = currentGoal.pose.position
    orientation = currentGoal.pose.orientation
    rospy.loginfo("currentGoalCallback id = %s, position [%f, %f, %f]"%(moveBaseGoal.header.frame_id, position.x, position.y, position.z))
    rospy.loginfo("currentGoalCallback orientation [%f, %f, %f]"%(orientation.x, orientation.y, orientation.z))

def feedbackCallback(feedback):
    rospy.loginfo("feedbackCallback id = %s, status = %8u"%(feedback.status.goal_id.id, feedback.status.status))

global moveController

def moveBaseKeyControl(string):
    global moveController
    rospy.loginfo("moveBaseKeyControl 0 = %s"%(string.data))
    if string.data == 'restart':
        rospy.loginfo("moveBaseKeyControl 1 = %s"%(string))
        moveController.restartGoal()
    elif string.data == 'clearmap':
        rospy.loginfo("moveBaseKeyControl 2 = %s"%(string))
        moveController.clearCostmap()
    elif string.data == 'stop':
        rospy.loginfo("moveBaseKeyControl 3 = %s"%(string))
        moveController.cancelHjmGoal()
        

def update_initial_pose(init):
    position = init.pose.pose.position
    orientation = init.pose.pose.orientation
    rospy.loginfo("update_initial_pose header seq = %d, frameid = %s"%(init.header.seq, init.header.frame_id))
    rospy.loginfo("update_initial_pose x = %f, y = %f, z = %f"%(position.x, position.y, position.z))
    rospy.loginfo("update_initial pose x = %f, y = %f, z = %f, w= %f"%(orientation.x, orientation.y, orientation.z, orientation.w))
    #for i in init.pose.covariance: 
    #   print i

if __name__ == "__main__":
    global moveController
   
    rospy.init_node('global_planner_listener', anonymous=True)
    
    moveController = MoveController()
  
    rospy.Subscriber("/cmd_vel", Twist, cmdVelcallback)
    rospy.Subscriber("/move_base_simple/goal", PoseStamped, goalCallback)
    rospy.Subscriber("/move_base/result", MoveBaseActionResult, resultCallback)
    #rospy.Subscriber("/move_base/status", GoalStatusArray, statusCallback)
    rospy.Subscriber("/move_base/cancel", GoalID, cancelCallback)
    rospy.Subscriber("initialpose", PoseWithCovarianceStamped, update_initial_pose)
    #rospy.Subscriber("/move_base/current_goal", PoseStamped, currentGoalCallback)
    #rospy.Subscriber("/move_base/feedback", MoveBaseActionFeedback, feedbackCallback)
    rospy.Subscriber("/jiamiaohe/move_base_control", String, moveBaseKeyControl)   

    #moveController.initPositionMethod()

    rospy.spin()
    
