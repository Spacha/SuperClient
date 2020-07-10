from SuperClient.Communication import *
from SuperClient.Log import Log
from SuperClient.UI import UI
from random import random

MULTIPART_LEN = 64

class Client:
	# client meta
	CLI_VERSION = 1.04
	filename = ''
	cid = ''

	# server details
	srv_address = ''
	srv_tcp_port = 0
	srv_udp_port = 0

	# connection handles
	tcp = None
	udp = None

	# options
	opt_enc = False
	opt_mul = False
	opt_par = False

	# error handling
	error = False
	error_msg = ''

	ERR_CUSTOM = 0
	ERR_INVALID_ARGS = 1
	ERR_TCP_RESPONSE = 2
	ERR_TCP_CONN = 3
	ERR_UDP_RESPONSE = 4

	# encryption settings
	keyset_len = 20
	keyset_en = []
	keyset_de = []

	verbose = False
	ui = None
	log = None

	def __init__(self):
		'''
		Client class constructor.
		'''
		self.error = False

		# construct the user interface class (ansi disabled for now)
		self.ui = UI(False)

		# preset options (can be changed from cmdline)
		self.opt_enc = True
		self.opt_mul = True
		self.opt_par = True


	def start(self, args):
		'''
		Start the client with required arguments <address> and <port>.
		The design approach is the following:

		All active methods must return a boolean. If a method returns True, it indicates
		that the program is operating normally. If one returns False, an error has
		occurred and the method must've set an error message @self.error_msg
		as well as @self.error flag.
		'''

		# validate arguments and set options accordingly
		if not self.validateArgs(args):
			return

		# construct the log class for detailed logging
		self.log = Log(self.ui, self.verbose)

		# Welcome!
		self.splash()

		self.ui.info("Fetching connection parameters...")

		# fetch parameters from the server using TCP
		if not self.fetchCommParams():
			return

		self.ui.info("Opening UDP connection...")
		
		# jump to the "main" loop!
		if not self.UDPLoop():
			return

		self.ui.info("Exchange over, quitting...\n")

		# successfully went through the pipeline!
		self.shutdown()


	#--------------------------------------------------
	# 				ACTIVE METHODS
	#--------------------------------------------------
	# Active methods are required to function in a specific way:
	# - If they function correctly, they must return True
	# - Otherwise, return @self.setError([ERR_MSG])
	# -------------------------------------------------

	def UDPLoop(self):
		'''
		Inits a UDP connection and keeps communicating
		with the server as long as needed.
		'''
		
		self.udp = UDPConnection(self.cid, self.srv_address, self.srv_udp_port, self.log)

		# enable UDP extra features
		if self.opt_enc: self.udp.enableEncryption(self.keyset_en, self.keyset_de)
		if self.opt_mul: self.udp.enableMultipart(MULTIPART_LEN)
		if self.opt_par: self.udp.enableParityCheck()

		# From now on, UDPConnection class takes care of
		# encrypting, decrypting, partitioning etc.

		# send initial UDP message
		self.udp.send('HELLO from ' + self.cid)

		# show some progress
		self.ui.info_ok("Success")
		self.ui.info("Waiting for challenges...")

		# this loop receives challenges from server, comes up with a 'solution'
		# and sends it back until server ends the session
		while True:

			# receive a message
			challenge, eom = self.udp.receive()

			# pass the challenge to a solver and get a solution (reverse order)
			solution = self.challengeSolver(challenge)
			
			# End Of Messaging --> break the loop
			if eom:
				self.ui.text(f" Server: \"{challenge}\"\n", leftPad=7, wrap=False)
				self.ui.resetNumbering()
				break

			# if not last message, answer to the challenge and keep going
			self.ui.numbered("Challenge accepted:")
			self.ui.indented("»", f"\"{challenge}\"")
			self.ui.indented("«", f"\"{solution}\"\n",)
		
			# send the solution back to the server (word reversed)
			self.udp.send(solution)

		# Success! Close the connection and leave.
		self.udp.close()
		return True


	def validateArgs(self, args):
		'''
		Takes care of validationg the required arguments
		as well as setting them as class variables.
		Invalid arguments causes an error to be set.
		'''
		self.filename = args[0]
		disableANSI = False

		try:
			# validate args[1], args[2]
			self.srv_address = str(args[1])
			self.srv_tcp_port = int(args[2])

			# options (optional, heh)
			if len(args) >= 4:
				opts = str(args[3])

				if ('n' in opts) or ('N' in opts):
					# set all options off
					self.opt_enc = False
					self.opt_mul = False
					self.opt_par = False
				else:
					# set options individually
					self.opt_enc = ('e' in opts) or ('E' in opts)
					self.opt_mul = ('m' in opts) or ('M' in opts)
					self.opt_par = ('p' in opts) or ('P' in opts)

			if len(args) >= 5:
				# enable
				if int(args[4]) == 0: disableANSI = True

		except Exception:
			# set a helpful error message and return false
			return self.setError(self.ERR_INVALID_ARGS)

		if not disableANSI:
			self.ui.enableANSI()
		
		return True

	
	def fetchCommParams(self):
		'''
		Fetches the parameters required for establishing
		a communication channel with the server.
		TODO: This method does quite a lot by itself...
		'''

		# 1. Setup Connection

		self.tcp = TCPConnection(self.srv_address, self.srv_tcp_port, self.log)

		try:
			# connect socket to given address and port
			self.tcp.connectToServer()
		except ConnectionRefusedError:
			# catch the exception if the connection refuses, exit
			return self.setError(self.ERR_TCP_CONN)

		# build up the request
		request = ['HELLO']

		# join optional arguments to the initial message
		if self.opt_enc: request[0] += ' ENC'
		if self.opt_mul: request[0] += ' MUL'
		if self.opt_par: request[0] += ' PAR'

		# connection ok, generate a keyset if needed
		if self.opt_enc:
			self.keyset_en = self.generateKeyset()
			request += self.keyset_en + ['.']

		
		# 2. Fetch the Parameters
		
		# send the initial message + keys
		# TCPConnection.send() takes in a list of messages to be transmitted
		self.tcp.send(request)

		# receive the parameters + keys
		response = []
		while True:

			# TCPConnection.receive() automatically disassembles the response into messages
			response += self.tcp.receive()

			# end of transmission is based on opt_enc option:
			# IF no encryption is used, end after one message,
			# OTHERWISE wait until a message with only dot ('.') is received
			if self.opt_enc and '.' not in response: continue
			
			break


		# 3. Handle the Response

		# parse response
		valid_parsed_response = self.parseCommParams(response)
		
		# invalid response received, let's exit with error
		if not valid_parsed_response:
			return self.setError(self.ERR_TCP_RESPONSE)
 
		# all good, unpack the parsed parts from the response
		cid, port, keys = valid_parsed_response

		self.srv_udp_port = port
		self.cid = cid

		# save the received decoding keyset
		if self.opt_enc:
			self.keyset_de = keys

		self.ui.info_ok("Successful TCP response from server: CID: {}, UDP port: {}".format(self.cid, self.srv_udp_port))

		# we are done here, close the connection
		self.tcp.close()
		return True


	#--------------------------------------------------
	# 				 UTILITY METHODS
	#--------------------------------------------------
	# Various helper methods for wrapping common tasks.
	#--------------------------------------------------

	def splash(self):
		'''
		Prints a heart-warming welcome before the shell fills of error traces.
		Using a home-made "UI library".
		'''
		self.ui.borderStart()
		
		self.ui.logo()
		self.ui.emptyLine()
		self.ui.description() 		# short description of the application

		self.ui.horLine()
		
		# Version history
		
		self.ui.text("_Version: {}".format(self.CLI_VERSION))
		self.ui.changelog()

		self.ui.horLine()

		# Feature list
		
		self.ui.text("Active features:", ul=True, leftPad=3)
		self.ui.text(
			"-_Encryption___[{}]".format('X' if self.opt_enc else '_'),
			clr = 'green' if self.opt_enc else '',
			leftPad = 4
		)
		self.ui.text(
			"-_Multipart____[{}]".format('X' if self.opt_mul else '_'),
			clr = 'green' if self.opt_mul else '',
			leftPad = 4
		)
		self.ui.text(
			"-_Parity_______[{}]".format('X' if self.opt_par else '_'),
			clr = 'green' if self.opt_par else '',
			leftPad = 4
		)
		
		self.ui.emptyLine()
		self.ui.borderEnd()
		self.ui.horLine(noPadding=True)
		self.ui.emptyLine()
		return

	def shutdown(self):
		'''
		Here we could make a cleanup of some kind if we expanded our program.
		'''
		# INFO: "Shutting down..."

		return


	def generateKeyset(self):
		'''
		Takes care of generating a new keyset for encryption. The keys 
		themselves are generated in another method so it's easily changeable.
		'''

		keys = []
		for i in range(self.keyset_len):
			keys.append( self.generateEncryptionKey() )

		return keys

	def generateEncryptionKey(self):
		'''
		Generate a single key using pseudo-random function. Here you
		can implement any other key generator if you like.
		'''
		chars = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

		words = []
		key_chars = [
			chars[int((100*random()) % 16)] * 64
		]

		return ''.join(key_chars)


	def parseCommParams(self, messages):
		'''
		Validate and parse communication parameters.
		TODO: Call @self.setError() here to set a more verbose error message before returning False.
		Success: return tuple containing: cid, port, keys)
		If no enc in use, keys list is empty.
		'''

		# this tells if the response was valid
		msg, cid, port, keys = None, None, None, []

		# first of all, check that at least some messages were received
		if not (isinstance(messages, list) and len(messages) > 0):
			# Validation error: "Invalid TCP response"
			return False

		# handle the initial message
		initial_msg_parts = messages[0].split(' ')
		try:
			msg = str(initial_msg_parts[0])
			cid = str(initial_msg_parts[1])
			port = int(initial_msg_parts[2])
		except:
			# Validation error: "Invalid TCP response"
			return False

		if msg != 'HELLO':
			# Validation error: "Invalid TCP response (HELLO)"
			return False

		if self.opt_enc:
			# get the keys (ignore initial message + end of transmission)
			keys = messages[1:self.keyset_len+1]

			# check that a valid amount of keys were received
			# TODO: possibly do some extra validation for the keys here
			if len(keys) is not self.keyset_len:
				# Validation error: "Invalid encryption keys received"
				return False

		return (cid, port, keys)


	def challengeSolver(self, challenge):
		'''
		Advanced multicore challenge solver.
		
		Nah, not really.  This takes in a string that has words separated
		by spaces, flips the order of the words and returns it.
		'''
		words = challenge.split(' ')

		# do the magic...
		words.reverse()

		# ...and join back to string!
		return ' '.join( words )

	
	def setError(self, err_code, msg=''):
		'''
		This method is a helper that sets an error to the client and prepares to exit.
		This method returns false because after calling this, we'll return
		false anyway so we can use this as boolean instead.
		'''

		# error code => error message relations
		if err_code == self.ERR_CUSTOM:
			msg = "Custom error message: \"{}\"".format(msg)
		elif err_code == self.ERR_INVALID_ARGS:
			msg = "Invalid arguments!\n_______\tusage: {} <server address> <server port> <options> <ansi>".format(self.filename)
		elif err_code == self.ERR_TCP_CONN:
			msg = "TCP connection refused. Please check your address and port."
		elif err_code == self.ERR_TCP_RESPONSE:
			msg = "Invalid response from TCP."
		elif err_code == self.ERR_UDP_RESPONSE:
			msg = "Invalid response from UDP."
		else:
			msg = "Unknown error!\nThis is probably our fault, be kind plz."

		self.error_msg = self.ui.error(msg, noPrint=True)
		self.error = True

		return False
