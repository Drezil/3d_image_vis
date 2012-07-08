#!/usr/bin/python
import cv2
import cv
import os, os.path
import sys
import getopt
import sqlite3
import time
import numpy
import networkx as nx

EIGENDATA_LIMIT = 50 # only use the first 30 eigenvectors/eigenvalues

"""
concept:
    1. (vec - avg) converted to eigenvectors-base => 5 Vectors per channel, 20 Vectors total.
    2. for every channel calculate the difference to all other images
	a) foreach image-pair create upper 5x5 triangle-matrix with vector-distance between pairwise vectors in channels of a and b
	b) save greatest entry over all matrices
	c) divide matrices by that factor
	d) distance between a and b is now the 2-norm of all matrix-entries. (upper triangle)
    3. save distances in a matrix
    4. use this matrix as 3dimensional graph-weights (0: loose, 1: identical match)
    5. calculate coordinates out of this graph (fruckterman_reingold_3d).
    
    faster approach:
    2. for every channel calculate the difference to all other images
	a) foreach image-pair create upper 5x5 triangle-matrix with vector-distance between pairwise vectors in channels of a and b
	b) distance between a and b is now the 1-norm or maximumns-norm of all matrix-entries. (upper triangle)
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

def getEigenBase(cursor):
	statement = "SELECT eigenvalue"
	for i in range(1,129):
		statement += ", d_%d" %i
	statement += " from eigendata"
	cursor.execute(statement)
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
			avg = numpy.array([r[1:]])
	
	return (numpy.asarray(eigenvalues), numpy.vstack(eigenbase), avg)
	
#TODO: get representants in eigenbase

def getRepresentants(name,channel,ieigenbase,cursor):
	statement = "SELECT d_1"
	for i in range(2,129):
		statement += ", d_%d" %i
	statement += " from image_cluster WHERE image=? and channel=?"
	cursor.execute(statement, (name, channel))
	res = cursor.fetchall()
	#convert to cv
	vecs = []
	ret = []
	for r in res:
		toappend = numpy.array([r])
		vec = cv.fromarray(toappend)
		realvec = cv.CreateMat(vec.rows,vec.cols,cv.CV_32FC1)
		cv.Convert(vec,realvec)
		vecs.append(realvec)
	for vec in vecs:
		ret.append(ieigenbase * numpy.transpose(numpy.asarray(vec)))
	return ret
	

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
	
def weightedNorm(a,b,weights,norm=2):
	sum = 0
	for i in range(0,len(a)):
		sum += (abs((a[i]-b[i]))*weights[i]) ** norm
	return numpy.float64(sum) ** (1.0/norm)

def setUpDatabase(database):
	if _debug == 1:
		print "setting up database..."
	c = conn.cursor()
	c.execute("DROP Table if exists image_coordinates");
        statement = "CREATE TABLE image_coordinates (image text, x double, y double, z double)"
        c.execute(statement)
        statement = "CREATE INDEX IF NOT EXISTS id_image_coordinates_image on image_coordinates (image ASC)"
        c.execute(statement)
        statement = "CREATE INDEX IF NOT EXISTS id_image_coordinates_coordinates on image_coordinates (x ASC, y ASC, z ASC)"
        c.execute(statement)
	conn.commit()
	c.close()

def save(names,coords,cursor,LIMIT):
	for i in range(0,len(names[:LIMIT])):
		(x,y,z) = coords[i]
		statement = "INSERT INTO image_coordinates VALUES (\'%s\',\'%f\',\'%f\',\'%f\')" % (names[i][0],x,y,z)
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
		if _debug == 1:
			print "reading out data..."
		namelist = getNames(c)
		channellist = getChannels(c)
		(eigval, eigbase, avg) = getEigenBase(c)
		(_, inveigbase) = cv2.invert(eigbase)
		inveigbase = numpy.matrix(inveigbase)
		processed = 0
		matrix = []
		LIMIT = len(namelist)
		length = min(LIMIT,len(namelist))
		start = time.time()
		last = start
		representants = dict()
		for name in namelist[:LIMIT]:
			representants[name[0]] = dict()
			for channel in channellist:
				representants[name[0]][channel[0]] = getRepresentants(name[0],channel[0],inveigbase,c)
		for name in range(0,len(namelist[:LIMIT])-1):
			processed += 1
			if _debug == 1:
				print "processing: (%d/%d)..." % (processed,length)
			#representants = dict()
			#for channel in channellist:
			#	representants[channel[0]] = getRepresentants(name[0],channel[0],inveigbase,c)
			row = [];
			for nameb in range(name+1,len(namelist[:LIMIT])):
				distance = []
				for channel in channellist:
					#representants_b = getRepresentants(nameb[0],channel[0],inveigbase,c)
					for i in range(0,len(representants[namelist[name][0]])):
						for j in range(i,len(representants[namelist[nameb][0]])):
							a = representants[namelist[name][0]][channel[0]][i] - numpy.transpose(avg)
							b = representants[namelist[nameb][0]][channel[0]][j] - numpy.transpose(avg)
							dist = weightedNorm(a,b,eigval,2)
							distance.append(dist)
				#dist now holds the distances in the upper triangle-matrix
				sum = 0;
				for d in distance:
					#just sum up - TODO: could be weighted by channel, channels could get normalized, etc.
					sum += d
				row.append(d)
			matrix.append(numpy.array(row))
			if _debug == 1:
				now = time.time()
				total = (length**2) / 2
				done = length*processed - processed**2 / 2
				print "took: %fs. ETA: %fs (%.2f%% done.)..." % (now-last,(now-start)/done*(total-done),done*100.0/total)
				last = now

		adjacency = matrix
		print "allocating graph"
		
		G = nx.Graph()
		max = 0
		for i in range(0,len(namelist[:LIMIT])-1):
			for j in range(0,len(namelist[:LIMIT])-i-1):
				if (adjacency[i][j] > max):
					max = adjacency[i][j]
		for i in range(0,len(namelist[:LIMIT])-1):
			for j in range(0,len(namelist[:LIMIT])-i-1):
				G.add_edge(i,i+j+1,weight=max-adjacency[i][j])
				G.add_edge(i+j+1,i,weight=max-adjacency[i][j])
		pos = nx.spring_layout(G,3)
		
		save(namelist,pos,c,LIMIT)
		conn.commit()
		
		if _debug == 1:
			print "done."
		
	except getopt.GetoptError:           
        	usage()                          
	        sys.exit(2)
