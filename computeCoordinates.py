#!/usr/bin/python
import cv2
import cv
import os, os.path
import sys
import getopt
import sqlite3
import time
import numpy

EIGENDATA_LIMIT = 50 # only use the first 30 eigenvectors/eigenvalues

	"""
	concept:
	    1. (vec - avg) converted to eigenvectors-base => 5 Vectors per channel, 20 Vectors total.
	    2. for every channel calculate the difference to all other images
		a) foreach image-pair create upper 5x5 triangle-matrix with vector-distance between pairwise vectors in channels of a and b
		b) save greatest entry over all matrices
		c) divide matrices by that factor
		d) distance between a and b is now the 2-norm of all matrix-entries. (üpper triangle)
	    3. save distances in a matrix
	    4. use this matrix as 3dimensional graph-weights (0: loose, 1: identical match)
	    5. calculate coordinates out of this graph (fruckterman_reingold_3d).
	    
	    faster approach:
	    2. for every channel calculate the difference to all other images
		a) foreach image-pair create upper 5x5 triangle-matrix with vector-distance between pairwise vectors in channels of a and b
		b) distance between a and b is now the 1-norm or maximumns-norm of all matrix-entries. (üpper triangle)
	    ...
	    4. use this matrix as 3dimensional graph-weights (0: loose, x: identical match), x >> 0
	    
	    
	    faster approach gets realized first,
	"""


def usage():
	print """
	-b		database
	--database
	-h		this message
	--help
	-v		print debug-msg.
	--verbose
"""

def getEigenBase(cursor)
	statement = "SELECT eigenvalue"
	for i in range(1,129):
		statement += ", d_%d" %i
	statement += " from eigendata"
	cursor.execute(statement, (name, channel))
	res = cursor.fetchall()
	#convert to cv
	eigenbase = []
	eigenvalues = []
	avg = []
	for r in res:
		if r[0] >= 0:
			#eigenbase
			toappend = numpy.array([r[1:]])
			#convert to 32 bit cv-matrix
			vec = cv.fromarray(toappend)
			realvec = cv.CreateMat(vec.rows,vec.cols,cv.CV_32FC1)
			cv.Convert(vec,realvec)
			eigenbase.append(realvec)
			#eigenvalue
			eigenvalues.append(r[0])
		else:
			#avg
			avg = numpy.array([r])
	
	#convert eigenvalues to 32 bit cv-matrix
	eigenvalvec = numpy.array([eigenvalues])
	vec = cv.fromarray(eigenvalvec)
	realvec = cv.CreateMat(vec.rows,vec.cols,cv.CV_32FC1)
	cv.Convert(vec,realvec)
	reteigenval = realvec
	
	#convert eigenvalues to 32 bit cv-matrix
	avgvec = numpy.array([eigenvalues])
	vec = cv.fromarray(avgvec)
	realvec = cv.CreateMat(vec.rows,vec.cols,cv.CV_32FC1)
	cv.Convert(vec,realvec)
	retavgvec = realvec
	return (reteigenval, cv.fromarray(numpy.vstack(eigenbase)), reitavgvec)
	
#TODO: get representants in eigenbase

def getRepresentants(name,channel,eigenbase,cursor):
	pass
	

def getNames(cursor):
	statement = "SELECT DISTINCT name from descriptors"
	cursor.execute(statement)
	res = cursor.fetchall()
	return res

def getChannels(cursor):
	statement = "SELECT DISTINCT channel from descriptors"
	cursor.execute(statement)
	res = cursor.fetchall()
	return res

def getVectors(name,channel,cursor):
	statement = "SELECT d_1"
	for i in range(2,129):
		statement += ", d_%d" %i
	statement += " from descriptors WHERE name=? and channel=?"
	cursor.execute(statement, (name, channel))
	res = cursor.fetchall()
	#convert to cv
	ret = []
	for r in res:
		toappend = numpy.array([r])
		vec = cv.fromarray(toappend)
		realvec = cv.CreateMat(vec.rows,vec.cols,cv.CV_32FC1)
		cv.Convert(vec,realvec)
		ret.append(realvec)
	return numpy.vstack(ret)
	
def setUpDatabase(database):
	if _debug == 1:
		print "setting up database..."
	c = conn.cursor()
	c.execute("DROP Table if exists image_cluster");
        statement = "CREATE TABLE image_cluster (image text, channel text "
        for i in range(1,129):
                statement += ", d_%d float" % i
        statement += ")"
        c.execute(statement)
        statement = "CREATE INDEX IF NOT EXISTS id_image_cluster_image on image_cluster (image ASC)"
        c.execute(statement)
        statement = "CREATE INDEX IF NOT EXISTS id_image_cluster_imagechannel on image_cluster (image ASC,channel ASC)"
        c.execute(statement)
	conn.commit()
	c.close()

def save(name, channel, kmean,cursor):
	#kmean = (retval,bestLables, centers)
	#-> just save centers.
	for mean in kmean[2]:
		statement = "INSERT INTO image_cluster VALUES (\'%s\',\'%s\'" % (name,channel)
        	for i in mean:
        		statement += ",%f" % i
        	statement += ")"
	        cursor.execute(statement)


if __name__=="__main__":
	print "incomplete!"
	sys.exit(1)
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
		if _debug == 1:
			print "reading out data..."
		namelist = getNames(c)
		channellist = getChannels(c)
		(eigval, eigbase, avg) = getEigenBase(c)
		processed = 0
		length = len(namelist)
		matrix = []
		for name in namelist:
			processed += 1
			if _debug == 1:
			print "Calculating representants for: (%d/%d)" % (processed,length)
			representants = getRepresentants(name[0],channel[0],eigbase,c)
			row = [];
			for nameb in namelist:
				if name[0] == nameb[0]:
					continue
				distance = []
				for channel in channellist:
					representants_b = getRepresentants(nameb[0],channel[0],eigbase,c)
					for i in range(0,len(representants)):
						for j in range(i,len(representants_b):
							a = cv2.subtract(representants[i],avg)
							b = cv2.subtract(representants_b[j],avg)
							dist = cv2.norm(a,b, cv2.NORM_L2)
							distance.append(dist)
				#dist now holds the distances in the upper triangle-matrix
				sum = 0;
				for d in distance:
					#just sum up - TODO: could be weighted by channel, channels could get normalized, etc.
					sum += d
				row.append(d)
			matrix.append(numpy.array([row]))
		adjacency = numpy.vstack(matrix)
		
		#TODO: calculate 3d-coords from graph-weights
		
		if _debug == 1:
			print "done."
		
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
