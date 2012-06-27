#!/usr/bin/python
import cv
import os, os.path
import sys
import getopt
import sqlite3
import time
import numpy

def usage():
	print """
	-b		database
	--database
	-h		this message
	--help
	-v		print debug-msg.
	--verbose
"""

def getVectors(cursor):
	global _debug
	if _debug == 1:
		print "reading out data..."
	statement = "SELECT d_1"
	for i in range(2,129):
		statement += ", d_%d" %i
	statement += " from descriptors"
	cursor.execute(statement)
	ret = cursor.fetchall()
	if _debug == 1:
		print "done."
	return ret
	
def setUpDatabase(database):
	if _debug == 1:
		print "setting up database..."
	c = conn.cursor()
	c.execute("DROP Table if exists eigendata");
        statement = "CREATE TABLE eigendata (eigenvalue float "
        for i in range(1,129):
                statement += ", d_%d float" % i
        statement += ")"
        c.execute(statement)
	conn.commit()
	c.close()

def save(eval,evec):
	for i in range(1,len(eval)):
		statement = "INSERT INTO eigendata VALUES (\"%f\"" % eval[i]
        	for ev in evec[i]:
        		statement += ",%f" % ev
	        #statement = statement[:len(statement)-2]
        	statement += ")"
	        cursor.execute(statement)


if __name__=="__main__":
	global _debug 
	_debug = 0
	try:
		database = "surf_descriptors.db"
		opts, args = getopt.getopt(sys.argv[1:], "hvb:", ["help", "verbose","database"])
		for opt, arg in opts:                
			if opt in ("-h", "--help"):      
				usage()                     
				sys.exit()                  
			elif opt in ("-v", "--verbose"):
				_debug = 1                  
			elif opt in ("-b", "--database"):
				database = arg
		if not os.path.isfile(database):
			print >> sys.stderr, "Database %s does not exist." % database
			sys.exit(1)
		conn = sqlite3.connect(database)
		setUpDatabase(database)
		c = conn.cursor()
		#covariance-matrix, 128x128
		if _debug == 1:
			print "calculating covariance after reading out data..."
		cov = numpy.corrcoef(getVectors(c), rowvar=0)
		#get eigenvalues and eigenvectors
		if _debug == 1:
			print "calculating eigenvalues/wigenvectors..."
		eval, evec = numpy.linalg.eig(cov)
		if _debug == 1:
			print "saving..."
		save(eval,evec)
		print "eigenvalues: %s" % eval[:30]
		print "eigenvectors: %s" % evec[:30]
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
