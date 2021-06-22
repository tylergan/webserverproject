'''
AUTHOR: Tyler Gan
Date: 21/11/2020

This program runs the server, which uses the read_config() function to read the configuration file, and send_data() to send the client appropriate output depending on the curl request
received.
'''

import sys, socket, os, time, threading
from io import StringIO

from server_functions import (
	read_config,
	send_data
)

def main():
	if (len(sys.argv[1:]) !=  1):
		print("Missing Configuration Argument")
		sys.exit(1)
	
	#READING DATA FROM THE CONFIG FILE =======================
	static_f_path, cgi_bin_path, port, exec_path = read_config(sys.argv[1]) 
	static_f_path, cgi_bin_path = os.path.abspath(static_f_path), os.path.abspath(cgi_bin_path)

	host, port = "127.0.0.1", int(port)

	static_files = [f for f in os.listdir(static_f_path) if os.path.isfile(os.path.join(static_f_path, f))] #obtain files located in static file path
	cgi_files = [f for f in os.listdir(cgi_bin_path) if os.path.isfile(os.path.join(cgi_bin_path, f))] #obtain files located in cgi bin path

	os.environ["SERVER_ADDR"] = host
	os.environ["SERVER_PORT"] = str(port)

	#SET UP SERVER AND CONNECTIONS =======================
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((host, port))
		s.listen(1)

		while True:
			conn, addr = s.accept()
			os.environ["REMOTE_ADDRESS"] = addr[0]
			os.environ["REMOTE_PORT"] = str(addr[1])

			threading._start_new_thread(send_data, (conn, cgi_files, cgi_bin_path, exec_path, static_files, static_f_path,)) #start a new thread, allowing for clients to use server concurrently (same time)

if __name__ == '__main__':
	main()