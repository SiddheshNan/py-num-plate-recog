import cv2
from datetime import datetime
import sys
import imutils

refPt = []
cropping = False

(width, height) = (150, 150)

cord_ls = []
order = {}
roi_ls = {}


def click_and_crop(event, x, y, flags, param):
    # grab references to the global variables
    global refPt, cropping

    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cropping = True

    # check to see if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates and indicate that
        # the cropping operation is finished
        refPt.append((x, y))
        cropping = False

        # draw a rectangle around the region of interest
        # print (refPt[0], refPt[1])
        cord_ls.append(refPt)
        cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
        cv2.imshow("image", image)


# construct the argument parser and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--image", required=True, help="Path to the image")
# args = vars(ap.parse_args())

# load the image, clone it, and setup the mouse callback function

count = 0
cam = int(sys.argv[1])
webcam = cv2.VideoCapture(cam)
# keep looping until the 'q' key is pressed
while True:
    ret, image = webcam.read()
    image = imutils.resize(image, width=400)
    clone = image.copy()
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)
    # display the image and wait for a keypress
    for idx, cord in enumerate(cord_ls):
        # print cord[0]
        order[idx] = cord
        cv2.putText(image, str(idx), (cord[0][0] - 10, cord[0][1] - 10),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
        cv2.rectangle(image, cord[0], cord[1], (0, 255, 0), 2)

    key = cv2.waitKey(1) & 0xFF
    # if the 'r' key is pressed, reset the cropping region
    if key == ord("r"):
        image = clone.copy()

    # if the 'c' key is pressed, break from the loop
    elif key == ord("c"):
        count += 1
        cv2.putText(image, 'ROI Selected...', (20, 20),
                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
        # if there are two reference points, then crop the region of interest
        # from teh image and display it
        # for key, cord in order.iteritems():
        #	if len(cord) == 2:
        #		roi = clone[cord[0][1]:cord[1][1], cord[0][0]:cord[1][0]]
        # roi_resize = cv2.resize(roi, (width, height))
        # roi_resize = cv2.cvtColor(roi_resize, cv2.COLOR_BGR2GRAY)
        # cv2.imshow("ROI"+str(key), roi_resize)
        cv2.imwrite("roi/ROI" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ".png", image)
    # roi_ls[key] = roi_resize
    cv2.imshow("image", image)
    if key == 27:
        break
print(order)
# close all open windows
cv2.destroyAllWindows()
