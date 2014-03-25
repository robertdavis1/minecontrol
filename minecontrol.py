#! /usr/bin/env python

# This python program was designed to maintain my mining rig utilizing cudaminer. It will check
#  to see if the miner is running and if not, start up the new cudaminer process.

import httplib
import urllib2
import socket
import sys
import base64
import argparse
import threading
import Queue
import subprocess
import psutil
import time
import logging
#from includes.healthchecks import *
from includes.util import *
from time import localtime, strftime
from ConfigParser import SafeConfigParser


# Main function
def main(config,pool):
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	outfile = '/home/miner/mining/minecontrol/miner.log'
	handler = logging.FileHandler(outfile)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter('%(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.info("---------------- Starting Minecontrol ----------------")
	logger.info("[*] Running minecontrol.py at %s" % (strftime("%a, %d %b %Y %H:%M:%S +0000", localtime())))
	
	# kill all cuda processes running before continuing
	logger.info("[*] Killing cudaminer processes: %s" % str(killCuda('')))
	
	if pool:
		logger.debug("[D] Manual pool set: %s" % pool)
	else:
		logger.debug("[D] Using config to pull pool data: %s" % config)
		cp = SafeConfigParser()
        	cp.optionxform = str # Preserves case sensitivity
        	cp.readfp(open(config, 'r'))
		main_section = 'Main'
                gpu_split = int(cp.get(main_section,'gpu_split'))
                if gpu_split == 0:
                        logger.info("[*] Hash split = 100% (or ZERO split)")
                elif gpu_split == 1:
                        logger.info("[*] Hash split = 50/50")
                else:
                        logger.info("[*] Hash split = unknown (using 100%)")
        	
		# Primary pool config
		primary_section = 'Primary'
        	primary_name = cp.get(primary_section,'name')
		primary_pool = cp.get(primary_section,'pool')
        	primary_port = cp.get(primary_section,'port')
		primary_worker = cp.get(primary_section,'worker')
		pri_worker_pw = cp.get(primary_section,'password')
		primary_connection = "stratum+tcp://%s:%s" % (primary_pool,primary_port)	

		# Secondary pool config
		secondary_section = 'Secondary'
                secondary_name = cp.get(secondary_section,'name')
                secondary_pool = cp.get(secondary_section,'pool')
                secondary_port = cp.get(secondary_section,'port')
		secondary_worker = cp.get(secondary_section,'worker')
                sec_worker_pw = cp.get(secondary_section,'password')
		secondary_connection = "stratum+tcp://%s:%s" % (secondary_pool,secondary_port)
	
		# Tertiary pool config
                tert_section = 'Tertiary'
                tert_name = cp.get(tert_section,'name')
                tert_pool = cp.get(tert_section,'pool')
		tert_port = cp.get(tert_section,'port')
                tert_worker = cp.get(tert_section,'worker')
                tert_worker_pw = cp.get(tert_section,'password')
		tert_connection = "stratum+tcp://%s:%s" % (tert_pool,tert_port)
		
		# Start the cudaminer process
		if gpu_split == 0:
			while True:
				if checkStratum(primary_pool,primary_port,primary_worker,pri_worker_pw):
					if not checkCuda(primary_connection):
						if checkCuda(secondary_connection):
							logger.info("[*] Secondary pool connected while primary is up. Killing secondary")
							killCuda(secondary_connection)
						logger.info("[*] Connecting to primary pool at %s" % primary_connection)
						subprocess.Popen(["cudaminer", "-S", "-o", primary_connection,"-u", primary_worker, "-p", pri_worker_pw], stdout=subprocess.PIPE)
					else:
						time.sleep(10)
				else:
					logger.info(" [!] Primary pool down!")
					if checkCuda(primary_connection):
						logger.info("[!] Killing primary connection...")
						killCuda(primary_connection)
					if checkStratum(secondary_pool,secondary_port,secondary_worker,sec_worker_pw):
						if not checkCuda(secondary_connection):
							logger.info("[!] Connecting to secondary pool at %s..." % secondary_connection)
							subprocess.Popen(["cudaminer", "-S", "-o", secondary_connection,"-u", secondary_worker, "-p", sec_worker_pw], stdout=subprocess.PIPE)
						else:
							time.sleep(10)
					else:
						logger.info("[!] Secondary pool down!!")
		elif gpu_split == 1:
			while True:
				if not checkCuda(primary_connection):
					logger.info("[*] Cudaminer starting for %s" % primary_connection)
					subprocess.Popen(["cudaminer", "-S", "-d0", "-o", primary_connection,"-u", primary_worker, "-p", pri_worker_pw], stdout=subprocess.PIPE)
					if not checkCuda(secondary_connection):	
						logger.info("[*] Cudaminer starting for %s" % secondary_connection)
						subprocess.Popen(["cudaminer", "-S", "-d1", "-o", secondary_connection,"-u", secondary_worker, "-p", sec_worker_pw], stdout=subprocess.PIPE)			
					time.sleep(10)	
				else:
					if not checkCuda(secondary_connection):	
						logger.info("[*] Cudaminer starting for %s" % secondary_connection)
						subprocess.Popen(["cudaminer", "-S", "-d1", "-o", secondary_connection,"-u", secondary_worker, "-p", sec_worker_pw], stdout=subprocess.PIPE)			
					
					#if not checkStratum(primary_pool,primary_port,primary_worker,pri_worker_pw):
                                        #	logger.info(" [!] Primary connection down. Connecting to tertiary...")
                                        #        subprocess.Popen(["cudaminer", "-S", "-d0","-o", tert_connection,"-u", tert_worker, "-p", tert_worker_pw], stdout=subprocess.PIPE)
					#else:
                                        #        time.sleep(5)
					#if not checkStratum(secondary_pool,secondary_port,secondary_worker,sec_worker_pw):
					#	logger.info(" [!] Secondary connection down. Connecting to tertiary...")
                                        #        subprocess.Popen(["cudaminer", "-S", "-d1","-o", tert_connection,"-u", tert_worker, "-p", tert_worker_pw], stdout=subprocess.PIPE)                                   
					#else:
					time.sleep(10)
		else: 
			logger.error("[X] No split found. Cudaminer not started\n")

# Start here
if __name__ == "__main__":
	pool = ""
        config = '/home/miner/mining/minecontrol/conf/mining.conf'
	parser = argparse.ArgumentParser(version="1.0",description="A cudaminer healthcheck and management script.")
        parser.add_argument('-p', help='Pool name', metavar='POOL',dest='pool')
        parser.add_argument('-c', help='Config file with pool lists; default: mining.conf', metavar='CONFIG',dest='config')
        args = parser.parse_args()
        if args.pool:
		pool = args.pool
	if args.config:
		config = args.config
	main(config, pool)
