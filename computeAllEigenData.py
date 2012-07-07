#!/usr/bin/python
import cv
import os, os.path
import sys
import getopt
import sqlite3
import time
import numpy

EIGENDATA_LIMIT = 50 # only use the first 30 eigenvectors/eigenvalues

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
	statement = "SELECT d_1"
	for i in range(2,129):
		statement += ", d_%d" %i
	statement += " from descriptors"
	cursor.execute(statement)
	res = cursor.fetchall()
	#convert to cv
	ret = []
	for r in res:
		toappend = numpy.array([r])
		ret.append(cv.fromarray(toappend))
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

def save(eval,evec,avg,cursor):
	for i in range(1,EIGENDATA_LIMIT):
		statement = "INSERT INTO eigendata VALUES (\"%f\"" % cv.Get1D(eval,i-1)[0]
        	for j in range(1,129):
        		statement += ",%f" % cv.Get2D(evec,i-1,j-1)[0]
	        #statement = statement[:len(statement)-2]
        	statement += ")"
	        cursor.execute(statement)
	#TODO: save AVG
	print "Todo: save AVG: %s" % avg


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
			print "reading out data..."
		cov = cv.CreateMat(128,128,cv.CV_64FC1)
		avg = cv.CreateMat(128,1,cv.CV_64FC1)
		vects = getVectors(c)
		if _debug == 1:
			print "calculating covariance..."
		cv.CalcCovarMatrix(vects,cov,avg,cv.CV_COVAR_NORMAL)
		#get eigenvalues and eigenvectors
		if _debug == 1:
			print "calculating eigenvalues/wigenvectors..."
		#128 times 128-dim eigenvec and 128 1-dim eigenvals
		eigvec = cv.CreateMat(128,128,cv.CV_64FC1)
		eigval = cv.CreateMat(128,1,cv.CV_64FC1)
		cv.EigenVV(cov,eigvec,eigval,10**(-15), 0, EIGENDATA_LIMIT)
		if _debug == 1:
			print "saving..."
		save(eigval,eigvec,avg,c)
		conn.commit()
		c.close()
		eval = []
		for i in range(1,EIGENDATA_LIMIT):
			eval.append(cv.Get1D(eigval,i-1)[0])
		print "eigenvalues: %s" % eval
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
