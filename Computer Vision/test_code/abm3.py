##--------------------------Import Statements-----------------------------##
import cv2			#Python bindings for OpenCV
import argparse                 #Allows the program to take arguments from the command line
import numpy as np		#API for matrix operations
#import math
#import multiprocessing as mp

##--------------------------Useful Information----------------------------##
    #flags for the threshold function, with their respective indices:
    # i.e: cv2.threshold(frame,127,255, 0)  where 0 is the flag below.
    #     The 127 - 255 are the threshold range
    #
    # 0 - cv2.THRESH_BINARY
    # 1 - cv2.THRESH_BINARY_INV
    # 2 - cv2.THRESH_TRUNC
    # 3 - cv2.THRESH_TOZERO
    # 4 - cv2.THRESH_TOZERO_INV


    #Example use of image denoising function dilate:
    # d_img = cv2.dilate(frame,kernel=None [,...]) It seems to work

  ##
  #The counting system is very fragile and simple. It is also very easily implemented
    # but it probably has less than 85% accuracy for counting vehicles. At least it is
    #able to run on the Raspberry Pi B if the right set up is present. 
##----------------------Setting up the Argument Parser----------------------##

parser = argparse.ArgumentParser(description='Finds the contours on a video file')          #creates a parser object
parser.add_argument('-p','--path',type=str,help="""A video filename or path.
Works better with .avi files.
If no path or name is provided, the camera will be used instead.""")        #instead of using metavar='--path', just type '--path'. For some reason the metavar argument was causing problems
parser.add_argument('-a','--minArea',type=int,help='The minimum area (in pixels) to draw a bounding box',
                    default=120)
parser.add_argument('-d','--direction', type=str,default='H',help="""A character: H or V
representing the orientation of the count line. H is horizontal, V is vertical.
If not provided, the default is horizontal.""")
parser.add_argument('-n','--numCount',type=int,default=10,help="""The number of contours to be detected by the program.""")
parser.add_argument('-w','--webcam',type=int,default=0,help="""Allows the user to specify which to use as the video source""")
parser.add_argument('-s','--show',type=int,default=1,help="""0 or 1 indicating if the windows for the
images should be displayed. 0 is False and 1 is True. The default value is 1""")

args=vars(parser.parse_args())



##-------------------------Function Definitions----------------------------##
def clickEvent(event,x,y,flags,userdata):
    global rect
    if event==cv2.EVENT_LBUTTONDOWN:
        rect.append((y,x))                  #Numpy manages the coordinates as (y,x) instead of (x,y) like the rest of the world

def clickEventPoly(event,x,y,flags,userdata):
    global poly
    if event==cv2.EVENT_LBUTTONDOWN:
        poly.append((x,y))


def findClosestPoint(p1,p2):
    '''Compares two points (2D) and returns their euclidean distance.
    It might be more efficient to use numpy's linalg.norm() function.'''

    dist = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    
    return dist
        
        
def boundObjects(frame,thresh):
    global counter,width,halfH,halfW,prev_x,prev_y,minArea,numCnts
    global p1_count_line,p2_count_line,font,ctrs,GUI
    cnts,_ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts,key = cv2.contourArea,reverse=True)[:numCnts]    

    index = 1
    current_cent = []       #a list for the centroids of the current frame
    for c in cnts:
        if cv2.contourArea(c) < minArea:
            continue

        rect = cv2.minAreaRect(c)
        points = cv2.cv.BoxPoints(rect)
        points = np.int0(points)

        #Getting the center coordinates of the contour box
        cx = int(rect[0][0])
        cy = int(rect[0][1])

        C = np.array((cx,cy))
        current_cent.append((cx,cy))        

        #Finding the centroid of c in the previous frame
        if len(ctrs)==0: prev_x,prev_y = cx,cy
        elif len(cnts)==0: prev_x,prev_y = cx,cy
        else:
            minPoint = None
            minDist = None
            for i in range(len(ctrs)):
                dist = np.linalg.norm(C-ctrs[i])                #numpy's way to find the euclidean distance between two points
                if (minDist is None) or (dist < minDist):
                    minDist = dist
                    minPoint = ctrs[i]
    
            prev_x,prev_y = minPoint
        #ctrs = current_cent

        
        #Determines if the line has been crossed
        if args['direction'].upper()=='H':
            if (prev_y <= p1_count_line[1] <= cy) or (cy <= p1_count_line[1] <= prev_y):
                counter += 1
                if GUI: cv2.line(frame,p1_count_line,p2_count_line,(0,255,0),3)
                #cv2.line(frame,p1_count_line,p2_count_line,(0,255,0),3)
                print (counter)
        elif args['direction'].upper()=='V':
            if (prev_x <= p1_count_line[0] <= cx) or (cx <= p1_count_line[0] <= prev_x):
                counter += 1
                if GUI: cv2.line(frame,p1_count_line,p2_count_line,(0,255,0),3)
                #cv2.line(frame,p1_count_line,p2_count_line,(0,255,0),3)
                print (counter)

        if GUI:
            cv2.drawContours(frame,[points],0,(0,255,0),1)
            cv2.line(frame,(prev_x,prev_y),(cx,cy),(255,0,0),1)         #A line to show motion
            #cv2.circle(frame,(cx,cy),3,(0,0,255),2)
            cv2.putText(frame,'('+str(cx)+','+str(cy)+')',(cx,cy),font,0.3,(0,255,0),1)
            cv2.putText(frame,str(index),(cx,cy-15),font,0.4,(255,0,0),2)

        index += 1
        
    ctrs = current_cent
    return frame

#def drawLine(frame,orientation='H',p1,p2,color=(0,0,255)):
#    if orientation.upper()=='H':
#        cv2.line(frame,p1...

##-----------------------Setting Initial Properties------------------------##
GUI = args['show']                          #A boolean indicating if the GUI should be used

##------------Initializing the Video Source------------##
if args.get('path',None) is None and args['webcam']==0:           #when a path is not provided, use camera
    cap = cv2.VideoCapture(0)
    #cap.set(3,320)
    #cap.set(4,240)
    #cap.set(3,160)
    #cap.set(4,120)
elif args['webcam'] != 0:
	cap = cv2.VideoCapture(args['webcam'])
	#cap.set(3,320)
	#cap.set(4,240)
else:
    cap = cv2.VideoCapture(args['path'])    #otherwise, use the given path or namec

##----------------------------------------------------------------------------##

_,img = cap.read()                          #gets the initial frame
img2 = img.copy()
img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
#average = np.float32(img)

##---------------Setting up ROI---------------------------------------
if GUI:
    manual_box = int(raw_input("""Select ROI manually or by entering (x,y), witdth and height?
Enter 1 for manual selection, 0 for exact values: """))
else: manual_box = 0

if manual_box:
    cv2.namedWindow('setup',1)
    k = None
    rect = []
    cv2.imshow('setup',img2)
    while k != ord('q') and k != 27:
        cv2.setMouseCallback('setup',clickEvent)
        k = cv2.waitKey(0) & 0xFF
    cv2.destroyWindow('setup')

    
    
    roi = np.array([rect])
    box = cv2.boundingRect(roi)
    x,y,w,h = box
else:
    size = raw_input("""Enter the ROI information:
x,y,w,h; where (x,y)is the left uppermost corner,
w is width, h is height. Enter the numbers separated by commas:
""")
    size = [int(n) for n in size.split(',')] 
    y,x,h,w = size              #x,y are switched because of the way numpy uses them for arrays
    

roi_mask = img[x:x+w,y:y+h]
poly = []
if manual_box:
    print('Now select the exact ROI you want')
    k=None
    cv2.namedWindow('setup2',1)
    cv2.imshow('setup2',roi_mask)
    while k!=ord('q') and k != 27:
        cv2.setMouseCallback('setup2',clickEventPoly)
        k = cv2.waitKey(0) & 0xFF
    cv2.destroyWindow('setup2')
    roi_poly = np.array([poly])

    
    print(poly)
if len(poly)!= 0:
    black_mask = np.zeros(roi_mask.shape,dtype=np.uint8)
    cv2.fillPoly(black_mask,roi_poly,(255,255,255))
cv2.imshow('selection',roi_mask)            #This and the next line are for debugging
cv2.waitKey(10) & 0xFF
average = np.float32(black_mask)

#---------------setting global variables---------------##
width = roi_mask.shape[1]
height = roi_mask.shape[0]
    
halfH = height/2                   #half of the height 
halfW = width/2                   #half of the width

threeFourthH = halfH + int(halfH/2)
threeFourthW = halfW + int(halfW/2)

#width = int(cap.get(3))
#height = int(cap.get(4))
prev_x,prev_y = 0,0
counter = 0                                 #global object counter
minArea = args['minArea']
numCnts = args['numCount']
rate = 0.01
ctrs = []                                   #a list of the centroids from the previous frames
font = cv2.FONT_HERSHEY_SIMPLEX
#frame_count = str(cap.get(7))
frame_num = 0                   #counts the current frame number
##----------------------------------------------------------------------------##

p1_count_line = None
p2_count_line = None

if args['direction'].upper()=='H' or args.get('direction',None) is None:
    p1_count_line = (0,halfH)
    p2_count_line = (width,halfH)
elif args['direction'].upper()=='V':
    p1_count_line = (halfW,0)
    p2_count_line = (halfW,height)
else: raise ValueError('Expected an "H" or a "V" only')

##-----------------------------------------------------------------------------------------##
#||||||||||||||||||||||||||||||||||||||| MAIN LOOP ||||||||||||||||||||||||||||||||||
##------------------------------------------------------------------------------------

while True:
    grabbed,img = cap.read()
    if not grabbed:
        break
#    elif frame_num < 120            #Hardcoded value indicating how many frames to let pass once the video begins
    

    #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    #--------------
    roi_mask = img[x:x+w,y:y+h]
    roi_mask = cv2.cvtColor(roi_mask,cv2.COLOR_BGR2GRAY)
    window_mask = cv2.bitwise_and(roi_mask,black_mask)
    #img2 = roi_mask.copy()

    #--------------
    if frame_num < 120:            #Hardcoded value indicating how many frames to let pass once the video begins
        frame_num += 1
        cv2.accumulateWeighted(window_mask,average,rate)
        continue
    cv2.accumulateWeighted(window_mask,average,rate)
    result = cv2.convertScaleAbs(average)       #the average background
    fmask = cv2.absdiff(result,window_mask)         #difference between the running average background and the current frame

  ##------Extra blur------##
    fmask = cv2.GaussianBlur(fmask,(21,21),0)
    fmask = cv2.blur(fmask,(28,28))

    _,thresh = cv2.threshold(fmask,30,255,0)

 ##-----Noise reduction-----##
 #   dimg = thresh
    dimg = cv2.erode(thresh,None)
    dimg = cv2.erode(dimg,None)
    dimg = cv2.dilate(dimg,None)                  #Noise reduction function
    dimg = cv2.dilate(dimg,None)
    
    #cv2.imshow('dilate',dimg)

#-------------------------------------------
    #Setting the boxes for the bounding process
    img2 = cv2.cvtColor(window_mask,cv2.COLOR_GRAY2BGR)
    boundObjects(img2,dimg)        

    #info = 'Frames processed: '+str(cap.get(1))+'/'+frame_count
    #cv2.putText(img2,info,(10,20),font,0.6,(0,255,0),2)
    
##---------------Showing The Frames-----------------##
    if GUI:
    
        cv2.imshow('roi',roi_mask)
        cv2.imshow('polygon',window_mask)
        #cv2.imshow('Original',img)
        cv2.imshow('average', result)
        #cv2.imshow('dilate',dimg)
        cv2.line(img2,p1_count_line,p2_count_line,(0,0,255),1)    
        cv2.imshow('boxes',img2)
        

##-------------Termination Conditions-------------##
    k = cv2.waitKey(30) & 0xFF
    if k == 27 or k == ord('q'):
        break

print(counter)
print(str(y),str(x),str(h),str(w))
cap.release()
cv2.destroyAllWindows()
