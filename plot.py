#!/usr/bin/python
import cv2
import cv
import os, os.path
import sys
import getopt
import sqlite3
import time
import numpy
from mayavi import mlab

def usage():
	print """
	-b		database
	--database
	-o		output file
	--outfile
	-h		this message
	--help
	-v		print debug-msg.
	--verbose
"""

def getCoords(cursor):
	statement = "SELECT image,x,y,z from image_coordinates"
	cursor.execute(statement)
	res = cursor.fetchall()
	names = []
	x = []
	y = []
	z = []
	i = 0
	for r in res:
		names.append(r[0])
		x.append(r[1])
		y.append(r[2])
		z.append(r[3])
	return (names,x,y,z)
	
if __name__=="__main__":
	global _debug 
	_debug = 0
	try:
		database = "surf_descriptors.db"
		outfile = "plot.png"
		opts, args = getopt.getopt(sys.argv[1:], "hvb:o:", ["help", "verbose","database","outfile"])
		for opt, arg in opts:                
			if opt in ("-h", "--help"):      
				usage()                     
				sys.exit()                  
			elif opt in ("-v", "--verbose"):
				_debug = 1                  
			elif opt in ("-b", "--database"):
				database = arg
			elif opt in ("-o", "--outfile"):
				database = arg
		if not os.path.isfile(database):
			print >> sys.stderr, "Database %s does not exist." % database
			sys.exit(1)
		conn = sqlite3.connect(database)
		c = conn.cursor()
		if _debug == 1:
			print "reading out data..."
		(names,x,y,z) = getCoords(c)
		
		mlab.points3d(x,y,z,range(0,len(names)), scale_mode="none", scale_factor=.01, mode="cube")
		mlab.show()
		
		if _debug == 1:
			print "done."
		
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
