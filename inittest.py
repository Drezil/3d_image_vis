#!/usr/bin/python
import cv
cv.SaveImage("testdata/test.png",cv.LoadImage("testdata/test.jpg"))
print "if there is no error, everything works!"
print "testing surf:"
im = cv.LoadImage("testdata/test.jpg")
(kp, desc) = cv.ExtractSURF(im, None, cv.CreateMemStorage(), (1, 5000, 3, 4))
print "found %d keypoints" % len(kp)
print "plotting keypoints"
for ((x, y), laplacian, size, dir, hessian) in kp:
	print "x=%d y=%d laplacian=%d size=%d dir=%f hessian=%f" % (x, y, laplacian, size, dir, hessian)
	cv.Circle(im,(int(x),int(y)),size,cv.RGB(255,0,0))
print "wrinting image with circles"
cv.SaveImage("testdata/test.png",im)
print "Done."
