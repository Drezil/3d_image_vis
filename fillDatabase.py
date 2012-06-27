#!/usr/bin/python
import cv
import os, os.path
import sys
import getopt
import sqlite3

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
	im = cv.LoadImage("testdata/test.jpg")
	return cv.ExtractSURF(im, None, cv.CreateMemStorage(), (1, 5000, 3, 4))

def savePoints(desc,conn):
	for d in desc:
		if len(d) != 128:
			print "ERROR: image has wrong size of descriptor"
			return
		c = conn.cursor()
		statement = "INSERT INTO descriptors VALUES ("
		for f in d:
			statement += "%f," % f
		statement = statement[:len(statement)-2]
		statement += ")"
		c.execute(statement)
		conn.commit()
		c.close()
	
def createDatabase():
	conn = sqlite3.connect('surf_descriptors.db')
	c = conn.cursor()
	statement = "CREATE TABLE descriptors (d_1 float"
	for i in range(2,129):
		statement += ", d_%d float" % i
	statement += ")"
	c.execute(statement)
	conn.commit()
	c.close()

if __name__=="__main__":
	try:
		datadir = None
		opts, args = getopt.getopt(sys.argv[1:], "hd:v", ["help", "dir","verbose"])
		for opt, arg in opts:                
			if opt in ("-h", "--help"):      
				usage()                     
				sys.exit()                  
			elif opt in ("-v", "--verbose"):
				global _debug               
				_debug = 1                  
			elif opt in ("-d", "--dir"): 
				datadir = arg  
		if datadir == None:
			print "-d must be present!"
			sys.exit(2)
		files = [f for f in os.listdir(datadir)
			if os.path.isfile(os.path.join(datadir, f))]
		i = 1
		length = len(files)
		if not os.path.isfile("surf_descriptors.db"):
			createDatabase()
		conn = sqlite3.connect('surf_descriptors.db')
		for f in files:
			(kp, desc) = pointImage(os.path.join(datadir,f))
			savePoints(desc, conn)
			print "done with file %d/%d: %s" % (i,len(files),os.path.join(datadir,f))
			i +=1
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
