#!/usr/bin/python
import cv
import os, os.path
import sys
import getopt
import sqlite3
import time


def usage():
	print """
	-d		dir to look for data
	--directory
	-b		database-file
	--database
	-h		this message
	--help
	-v		print debug-msg.
	--verbose
"""
def pointImage(file):
	try: 
		bwim = cv.LoadImage(file, iscolor=cv.CV_LOAD_IMAGE_GRAYSCALE)
		cim = cv.LoadImage(file, iscolor=cv.CV_LOAD_IMAGE_COLOR)
		size = cv.GetSize(cim)
		red = cv.CreateImage(size,cv.IPL_DEPTH_8U,1)
		green = cv.CreateImage(size,cv.IPL_DEPTH_8U,1)
		blue = cv.CreateImage(size,cv.IPL_DEPTH_8U,1)
		cv.MixChannels([cim],[red,green,blue], [
			(0,0), #cim.red -> red
			(1,1), #cim.green -> green
			(2,2)  #cim.blue -> blue
		])
		return [
			("bw", cv.ExtractSURF(bwim, None, cv.CreateMemStorage(), (1, 250, 3, 4))),
			("r", cv.ExtractSURF(red, None, cv.CreateMemStorage(), (1, 250, 3, 4))),
			("g", cv.ExtractSURF(green, None, cv.CreateMemStorage(), (1, 250, 3, 4))),
			("b", cv.ExtractSURF(blue, None, cv.CreateMemStorage(), (1, 250, 3, 4)))
		]
		    
	except Exception as e:
		print >> sys.stderr, "\033[1;31mERROR: cannot read/extract SURF out of %s: %s\033[0m\nIs the Image a 24Bit RGB-Image?" % (file, e)
		return [
			("bw", ([],[])),
			("r", ([],[])),
			("g", ([],[])),
			("b", ([],[]))
		]

def savePoints(file, desc, channel, cursor):
	for d in desc:
		if len(d) != 128:
			print "ERROR: image has wrong size of descriptor"
			return
		statement = "INSERT INTO descriptors VALUES ('%s','%s'" % (file,channel)
		for f in d:
			statement += ",%f" % f
		#statement = statement[:len(statement)-2]
		statement += ")"
		cursor.execute(statement)
	
def createDatabase(database):
	print "creating database in file '%s'" % database
	conn = sqlite3.connect(database)
	c = conn.cursor()
	statement = "CREATE TABLE descriptors (name text, channel text"
	for i in range(1,129):
		statement += ", d_%d float" % i
	statement += ")"
	c.execute(statement)
        statement = "CREATE INDEX IF NOT EXISTS id_descriptors_name on descriptors (name ASC)"
        c.execute(statement)
        statement = "CREATE INDEX IF NOT EXISTS id_descriptors_namechannel on descriptors (name ASC,channel ASC)"
        c.execute(statement)
	conn.commit()
	c.close()

if __name__=="__main__":
	try:
		datadir = None
		database = "surf_descriptors.db"
		opts, args = getopt.getopt(sys.argv[1:], "hd:vb:", ["help", "dir","verbose","database"])
		for opt, arg in opts:                
			if opt in ("-h", "--help"):      
				usage()                     
				sys.exit()                  
			elif opt in ("-v", "--verbose"):
				global _debug               
				_debug = 1                  
			elif opt in ("-d", "--dir"): 
				datadir = arg
			elif opt in ("-b", "--database"):
				database = arg
		if datadir == None:
			print "-d must be present!"
			sys.exit(2)
		print "reading data from %s..." % datadir
		files = [f for f in os.listdir(datadir)
			if os.path.isfile(os.path.join(datadir, f))]
		i = 1
		length = len(files)
		if not os.path.isfile(database):
			createDatabase(database)
		conn = sqlite3.connect(database)
		c = conn.cursor()
		for f in files:
			print "processing file \033[0;35m%d\033[0m/\033[0;32m%d\033[0m: %s" % (i,len(files),os.path.join(datadir,f))
			now = time.time()
			surf = pointImage(os.path.join(datadir,f))
			for (channel,(kp, desc)) in surf:
				savePoints(f, desc, channel, c)
			duration = time.time() - now
			print "done. Took \033[0;36m%fs\033[0m for %d descriptors" % (duration,len(desc))
			if i % 100 == 0:
				conn.commit()
			i +=1
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
