'''
AUTHOR: Tyler Gan
Date: 21/11/2020

This program contains all the functions needed to run the server. All of the functions (except for send_data() and read_config()) are used here to help run the main function, send_data().
'''

import sys, socket, sys, os, time, gzip, io

content_types = {
	"txt": "text/plain",
	"html": "text/html",
	"js": "application/javascript",
	"css": "text/css",
	"png": "image/png",
	"jpg": "image/jpeg",
	"jpeg": "image/jpeg",
	"xml": "text/xml"
}

def read_config(filename):
	'''
	Method that reads a configuration file and returns it if the configuration file is valid.
	'''
	try:
		with open(filename, 'r') as f:
			contents = [data.strip().split("=") for data in f.readlines()]
			
			if (len(contents) < 4):
				print("Missing Field From Configuration File")
				sys.exit(1)

			if ("staticfiles" not in contents[0] or "cgibin" not in contents[1] or "port" not in contents[2] or "exec" not in contents[3]):
				print("Missing Field From Configuration File")
				sys.exit(1)
			
			for elem in contents:
				elem = [obj for obj in elem if (obj != "")]
				
				if (len(elem) !=  2):
					print("Missing Field From Configuration File")
					sys.exit(1)
			
			contents = [data[1] for data in contents]

	except FileNotFoundError:
		print("Unable To Load Configuration File")
		sys.exit(1)

	return contents


def check_file(check_f, ls):
	'''
	A method that takes in a list of already found files and a file that is being requested, and returns either the filename or None, depending on whether the file is found
	'''
	for f in ls:
		if f in check_f:
			return f
	
	return None

def read_static_f(path, static_f_path):
	'''
	Method that takes a in path to a static file, reads the file using the given path, and returns the data as either a string or binary (if an image)
	'''
	path = os.path.join(static_f_path, path)

	f_type = os.environ["CONTENT_TYPE"]
	photo_type = ["png", "jpg", "jpeg"]

	os.environ["STATUS_CODE"], os.environ["STATUS_MSG"] = str(200), "OK" #as we have determined ALREADY that the file does exist.

	return "".join(open(path, 'r').readlines()).rstrip() if (f_type not in photo_type) else open(path, "rb").read()

def parse_http_req(temp_data):
	'''
	Method that parses an HTTP requests and assigns the appropriate information to environment variables
	'''
	REQ_METHODS = ["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]

	for data in temp_data:
		og_data = data
		data = data.split(" ")
		data[0] = data[0].upper().strip(":")

		if (data[0] in REQ_METHODS):
			os.environ["REQUEST_METHOD"] = data[0]

			if (data[1] == "/"):
				os.environ["REQUEST_URI"] = "index.html"
				os.environ["CONTENT_TYPE"] = "html"
			else:
				os.environ["REQUEST_URI"] = data[1]

				#check if there is also a query string attached to the content type
				content_type = data[1].split(".")[1]
				content_type = content_type.split("?") if ("?" in content_type) else content_type
				
				if (isinstance(content_type, list)):
					os.environ["QUERY_STRING"] = content_type[1]
					os.environ["CONTENT_TYPE"] = content_type[0]

				else:
					os.environ["CONTENT_TYPE"] = content_type

			os.environ["HTTP_PROTOCOL"] = data[2]

		else:
			if ("ACCEPT" == data[0]):
				os.environ["HTTP_ACCEPT"] = data[1]

			elif ("HOST" == data[0]):
				os.environ["HTTP_HOST"] = data[1]

			elif("USER-AGENT" == data[0]):
				os.environ["HTTP_USER_AGENT"] = data[1]

			elif ("ACCEPT-ENCODING" in data[0]):
				os.environ["HTTP_ACCEPT_ENCODING"] = data[0].split(":")[1].lower()
			
			elif ("CONTENT_LENGTH" == data[0]):
				os.environ["HTTP_CONTENT_LENGTH"] = data[1]

def exec_cgi(exec_path, process_param):
	'''
	Method that takes in an exec path and process paramaters to run a CGI program
	'''
	r, w = os.pipe()
	pid = os.fork()
	try:
		if (pid > 0):
			# parent 
			time_lim = 55 
			for _ in range(time_lim): #wait 55 seconds for the child to return a value other than 0
				child_pid, status = os.waitpid(-1, os.WNOHANG)

				if (child_pid != 0):
					break

				time.sleep(1)
			#store output from the child
			os.close(w)
			output = os.fdopen(r)

		elif (pid == 0):
			#child
			os.close(r)
			#duplicate stdout and stderr to the parent
			os.dup2(w, 1)
			os.dup2(w, 2)
			os.execv(exec_path, process_param)

		else:
			status = 1

	except ChildProcessError:
		status = 1

	#return appropriate data depending on the status of the exec process
	if (status != 0):
		return None
	else:
		os.environ["STATUS_CODE"], os.environ["STATUS_MSG"] = str(200), "OK"
		return output.read().strip()

def error_msg(status_code):
	'''
	Method that formats error message data if any process fails, such as an inability to find a file or successfully run a file
	'''
	status_msg = ""

	if (status_code == 404):
		os.environ["STATUS_CODE"], os.environ["STATUS_MSG"] = str(404), "File not found"
		body_msg = "Not Found"
	else:
		os.environ["STATUS_CODE"], os.environ["STATUS_MSG"] = str(500), "Internal Server Error"
		body_msg = "Server Error"
	
	msg = """\
<html>
<head>
\t<title>{} {}</title>
</head>
<body bgcolor="white">
<center>
\t<h1>{} {}</h1>
</center>
</body>
</html>""".format(os.environ["STATUS_CODE"], body_msg, os.environ["STATUS_CODE"], body_msg)

	return msg

def gzip_data(data):
	'''
	Method that will GZIP data if an encoding request for GZIP is done
	'''
	out = io.BytesIO()

	data = data.encode() if (isinstance(data, str)) else data

	with gzip.GzipFile(fileobj=out, mode = 'w') as f:
		f.write(data)
	
	data = out.getvalue()
	return data


def format_data(data):
	'''
	Method that formats data received from running a CGI program or from static files
	'''
	#need to filter out what headers get sent out
	global content_types

	try:
		header = "Content-Type: {}".format(content_types[os.environ["CONTENT_TYPE"]])
	except KeyError:
		header = "Content-Type: {}".format(content_types["html"]) #it could be a CGI or root file resource
	
	try:
		if (os.environ["HTTP_ACCEPT_ENCODING"] == "gzip"): #check if we are accepting an encoding
			header += "\nAccept-Encoding: {}".format(os.environ["HTTP_ACCEPT_ENCODING"])
			data = gzip_data(data)
	except KeyError:
		pass

	if ("Status-Code" in str(data)): #check if there is already a pre-defined status code in the CGI program
		tempData = data.split(" ")
		
		#Format any programs that contains a custom status 
		status_msg, new_data = [], []
		obtain_data = False
		for elem in tempData:
			if (tempData.index(elem) in [0, 1]):
				continue #ignore first character as that is just "Status-Code" and the other is the status code, which we assign later

			if ("\n" in elem): #as custom status is first line, it should be separated from data with a newline
				status_msg.append(elem.split("\n")[0]) #obtain all characters before the newline
				new_data.extend(elem.split("\n")[1:]) #add any after the newline to the data body
				obtain_data = True

			elif (not obtain_data):
				status_msg.append(elem)

			else:
				new_data.append(elem)

		data = " ".join(new_data) if (len(new_data) != 0) else data
		
		os.environ["STATUS_CODE"] = tempData[1]
		os.environ["STATUS_MSG"] = " ".join(status_msg)

	msg = "{} {} {}\n".format(os.environ["HTTP_PROTOCOL"], os.environ["STATUS_CODE"], os.environ["STATUS_MSG"]).encode() #add first line of response.
	msg = msg + ("{}\n\n".format(header)).encode() if ("Content-Type:" not in str(data)) else msg #add a header if not already present in data 
	msg = msg + data if (not isinstance(data, str)) else msg + ("{}\n".format(data)).encode() #add encoded data if data is not an IMG, otherwise just add IMG data instead as it is already encoded

	return msg

def send_data(conn, cgi_files, cgi_bin_path, exec_path, static_files, static_f_path):
	'''
	The main server which runs the entire program using a connection. Through the use of other arguments, data is obtained and sent back to the client
	'''
	with conn:
		data = conn.recv(1024)
				
		temp_data = [data.strip("\r") for data in data.decode().strip().split("\n")]
		parse_http_req(temp_data)
				
		#DETERMINE IF WE ARE GETTING A CGI PROCESS OR STATIC FILE =======================
		new_data = ""
		if ("cgibin" in temp_data[0]):
			f = check_file(os.environ["REQUEST_URI"], cgi_files) #look for file

			if (f != None): #file has been found
				#set up parameters for exec process
				if (os.environ["CONTENT_TYPE"] == "py"):
					exec_path = "/usr" + exec_path

				f = os.path.join(cgi_bin_path, f)
				process_param = [exec_path, f]

				new_data = exec_cgi(exec_path, process_param) #exec CGI process

				if (new_data == None):
					#the CGI process did not run successfully. Return 500 Internal Server error
					new_data = error_msg(500)

			else:
				#we did not find the file. Return 404 File Not Found error
				new_data = error_msg(404)

		else:
			#just print out the data of the static file
			f = check_file(os.environ["REQUEST_URI"], static_files)

			if (f != None):
				#return contents of the file
				new_data = read_static_f(f, static_f_path)

			else:
				#print another errror msg
				new_data = error_msg(404)

		data = format_data(new_data)
				
		conn.sendall(data)

	conn.close()