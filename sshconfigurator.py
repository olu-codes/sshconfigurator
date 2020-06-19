import re
import os.path
import os
import subprocess
import paramiko
import socket
import time
import threading

### THIS PROGRAM IS COPYRIGHTED BY OLUWASEYI BELLO, DO NOT REDISTRIBUTE OR ELSE I FREEZE YOUR LAPTOP :) JUST KIDDING! ENJOY!!!###
### PART1 GET THE IP ADDRESSES FROM THE FILE AND CHECK IF THEY ARE REACHABLE, RETURN A LIST CONTAINING OBTAINED IP ADDRESSES
def getips():
	
	iplist = []
	#attempt to open the file and read, check for validity of the file and the contents 
	while True:	
		try:
			check = True
			filename = raw_input("Enter the File containing the IP addresses: ")
			file = open(filename, "r")
			file.seek(0)
			#print("Successfully Opened the file")
			
			contents = file.readlines()
			file.close()
			
			for eachline in contents:
				eachline = eachline.strip(" ")
				eachline = eachline.strip("\n")
				
				regexp = re.match(r"^\d+.\d+.\d+.\d+$", eachline)
				if (regexp):				
					octets = eachline.split(".")
					a,b,c,d = int(octets[0]), int(octets[1]), int(octets[2]), int(octets[3])
					#print octets
					if len(octets) == 4 and (1 <= a <= 223) and (a != 127) and (0 <= b <= 255) and (0 <= c <= 255) and (0 <= d <= 255) and (a != 169 or b != 254):
						#print("The IP in the file is valid")
						iplist.append(eachline)
				
					else:
						#print("The IP in the file is not valid, check again")
						check = False	
				else:
					#print("Invalid Entry in file")
					check = False
					continue
				
			if check:
				break
			else:
				print("invalid Entry in file")
				
		except IOError:
			print("An error occurred in reading the file, check again")
			continue	
	'''			
	validips,unreachableiplist,reachableiplist = checkipreachability(iplist)
	unreachableips = ""
	for eachip in unreachableiplist:
		unreachableips += eachip + "\n"
		
	if validips == False:
		ans = raw_input("The following IPs were not reachable\n" + unreachableips + "Do you want to continue? (y/n)")
		if ans == 'N' or ans == 'n':
			getips()
		elif ans == 'Y' or ans == 'y':
			unreachableipsfile = open("unreachableips.txt","w+")
			unreachableipsfile.seek(0)
			for eachip in unreachableiplist:
				unreachableipsfile.write(eachip + "\n")
			unreachableipsfile.close()
			
	'''		
		
	return iplist

##PART2 GET CREDENTIALS FROM THE FILE,RETURN A LIST CONTAING TUPLES OF THE USERNAME, PASSWORD AND ENABLE PASSWORD IF ANY
def getcredentials():

	userlist = []
	while True:
		
		try:
			check = True
			filename = raw_input("Enter the filename containing the credentials: ")
			
			file = open(filename, "r")
			file.seek(0)
			
			users = file.readlines()
			file.close()
			
			if users:				
				#print users
				for eachuser in users:
					regexp = re.match(r"(.+),(.+)",eachuser)
					eachuser = eachuser.strip("\n")
					eachuser = eachuser.strip(" ")
					#print eachuser
					if regexp:
						userlist.append(tuple(eachuser.split(",")))
				
					else:
						print("invalid content, ensure the contents are in the format username,password")
						check = False
			else:
				print("Empty file, try again")
				check = False
		except IOError:
			print("An error occurred in reading the file, check again")
			check = False
		
		if check:
			break
	return userlist

#PART3 GET THE CONFIG FILE AND CHECK IF IT EXISTS AND CAN BE READ
def getconfigfile():	
	filename = ""
	while True:
		try:		
			filename = raw_input("Enter the configuration file: ")
			if os.path.exists(filename):
				print("file exists")				
				file = open(filename,"r")
				file.seek(0)				
				break
			else:
				print("file doesn't exist, try again")
		except IOError:
			print("file can't be read, try again")
		
	return filename

## FUNCTION TO CHECK THE REACHABILITY OF AN IP ADDRESS, TAKES A LIST OF IP ADDRESSES AS ARGUMENT AND RETURNS LIST OF REACHABLE IPS, 
## UNREACHABLE IPS AND A BOOLEAN VALUE INDICATING WHETHER ALL IPS COULD BE REACHED
def checkipreachability(ips):
	check = True
	unreachableips = []
	reachableips = []
	threads = []

	for eachip in ips:
		returncode = subprocess.call("ping " + eachip)
		if returncode == 0:
			#print eachip + " is reachable"
			reachableips.append(eachip)
		else:
			#print eachip + " is unreachable"
			unreachableips.append(eachip)
			check = False
	return check,unreachableips,reachableips

	
##FUNCTION TO CONFIGURE CISCO DEVICES USING SSH. TAKES A LIST OF IP ADDRESSES, A LIST OF USERNAMES CONTAINING TUPLES OF USERNAME, PASSWORD, ENABLE(IF ANY)
##AND THE NAME OF THE FILE TO BE READ FROM.
##SAVES THE CONFIGURATION ON THE DEVICES WHEN DONE
def configureciscodevicessh(ip, usernames, configfile):
	session = paramiko.SSHClient()
	session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	
	for eachuser in usernames:
		try:
			#print "using " + eachuser[0] + " to login to " + ip
			session.connect(ip, username = eachuser[0], password = eachuser[1])
			conn = session.invoke_shell()
			print "Successfully connected to %s using %s" % (ip,eachuser[0])
			output = conn.recv(65535)
			#print output
			
			regexp = re.search(r"(.+[>])",output,re.I)
			if regexp:
				conn.send("enable\n")
				time.sleep(10)
				output = conn.recv(65535)
				#print output
				if("Password:" in output or "PASSWORD:" in output):
					#print "enable password is required for device", ip
					try:
						#print eachuser[2]
						conn.send(eachuser[2] + "\n")
						time.sleep(5)
						output = conn.recv(65535)
						#print output
					except IndexError:
						print "enable password required for %s but none specified" % (ip)					
			
			conn.send("terminal length 0\n")
			time.sleep(10)
			conn.send("configure terminal\n")
			time.sleep(10)
			
			file = open(configfile,"r")
			file.seek(0)
			config = file.readlines()
			file.close()
			
			for eachline in config:
				conn.send(eachline + "\n")
				time.sleep(10)
				
			conn.send("end\n")
			time.sleep(10)
			conn.send("write memory\n")
			time.sleep(10)
			output = conn.recv(65535)
			#print output
			
			if "Invalid input detected at" in output:
				print "An Error occurred when configuring", ip, "check configuration file again.\n"
			
			else:
				print "Successfully configured",ip,"\n"
			
			break	
			
		except socket.error:
			print "Can't reach device " + ip + "\n"
			break
		except paramiko.ssh_exception.AuthenticationException:
			#print "Authentication failed for",eachuser[0],"to",ip
			pass
	
##PART4 CONFIGURE THE CISCO DEVICES EACH IP ADDRESS ON A SEPARATE THREAD.
def configuredevices(ips,usernames,configfile):			
	threads = []
	for eachip in ips:		
		th = threading.Thread(target = configureciscodevicessh, args = (eachip, usernames,configfile))
		th.start()
		threads.append(th)
	for eachthread in threads:
		eachthread.join()
				
	
ips = getips()		
usernames =  getcredentials()
#print usernames
configfile =  getconfigfile()
#print configfile
configuredevices(ips,usernames,configfile)

			
	
