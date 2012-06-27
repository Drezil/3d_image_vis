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
	-h		this message
	--help
	-v		print debug-msg.
	--verbose
"""
def pointImage(file):
	im = cv.LoadImage(file)
	return cv.ExtractSURF(im, None, cv.CreateMemStorage(), (1, 5000, 3, 4))

def savePoints(file, desc, cursor):
	for d in desc:
		if len(d) != 128:
			print "ERROR: image has wrong size of descriptor"
			return
		statement = "INSERT INTO descriptors VALUES (\"%s\"" % file
		for f in d:
			statement += ",%f" % f
		#statement = statement[:len(statement)-2]
		statement += ")"
		cursor.execute(statement)
	
def createDatabase(database):
	print "creating database in file '%s'" % database
	conn = sqlite3.connect(database)
	c = conn.cursor()
	statement = "CREATE TABLE descriptors (name text"
	for i in range(1,129):
		statement += ", d_%d float" % i
	statement += ")"
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
			print "processing file %d/%d: %s" % (i,len(files),os.path.join(datadir,f))
			now = time.time()
			(kp, desc) = pointImage(os.path.join(datadir,f))
			savePoints(f, desc, c)
			duration = time.time() - now
			print "done. Took %fs for %d descriptors" % (duration,len(desc))
			if i % 100 == 0:
				conn.commit()
			i +=1
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
