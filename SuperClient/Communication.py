'''
	SuperClient/Communication.py
	This file contains classes needed to start and manage communication with
	TCP and UDP servers. The classes are actually abstraction layers for
	socket library and their API is very simple. All you have to do is
	open a connection, pass a list of messages and you receive a list
	of response messages. The classes take care of all the dirty
	details such as en/decryption, multiparting and so on.
'''

import socket
import struct

RECV_BYTES = 4096 						# max bytes received from sockets
MSG_DELIMETER = '\r\n' 					# separates messages
STRUCT_FORMAT = '!8s??HH128s' 			# find details from UDPConnection.pack()
ENCODING = 'utf-8' 						# character encoding

class TCPConnection:
	'''
	This class is just an abstraction layer for sockets so that whoever uses
	this, doesn't need to know about sockets. Unless something goes wrong
	as often tends to happen in the world of programming...
	Communicates with a server using TCP.
	'''
	addr = ''
	port = 0
	sock = None
	log = None

	def __init__(self, addr, port, log):
		'''
		Constructs an istance of the class and creates a TCP socket.
		'''
		self.addr = addr
		self.port = port
		self.log = log

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		return

	def connectToServer(self):
		'''
		Simply connects the socket to the configured server.
		'''
		self.sock.connect((self.addr, self.port))
		return

	def send(self, messages):
		'''
		@messages is a list of strings to be sent.
		'''

		# encode the messages and join as a string
		request = MSG_DELIMETER.join(messages).encode(ENCODING)

		# send the request
		self.sock.sendall(request)

		
	def receive(self):
		'''
		Receive a TCP message and split it into pieces by MSG_DELIMETER.
		Returns a list of messages.
		'''
		response = self.sock.recv(RECV_BYTES)

		# split the response into individual messages
		messages = response.decode(ENCODING).split(MSG_DELIMETER)

		self.log.received_tcp(messages)

		# return a list of messages (strings)
		return messages

	def close(self):
		'''
		Simply close the socket.
		'''
		self.sock.close()
		return


class UDPConnection:
	'''
	This class is first of all an abstraction layer for sockets (the client doesn't
	need to know their existence) but can also work in different modes based on
	what options were set. These modes include encryption, multipart messages
	and parity bits (error detection).
	Communicates with a server using UDP with some toppings.
	'''
	cid = ''
	addr = ''
	port = 0
	sock = None
	log = None

	# options change the behaviour of the model
	opt_enc = False 		# encryption
	opt_mul = False 		# multipart messages
	opt_par = False 		# parity bit
	enc_keys_de = [] 		# encryption keyset (for decrypting)
	enc_keys_en = [] 		# encryption keyset (for encrypting)
	mul_len = 64 			# multipart maximum message length

	def __init__(self, cid, addr, port, log):
		'''
		Constructs an instance of the class and creates a UDP socket.
		'''
		self.cid = cid
		self.addr = addr
		self.port = port
		self.log = log

		# create the socket and return
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		return


	def send(self, message, ack=True):
		'''
		Send a UDP message to the configured server. Takes in a list of messages
		and manipulates them according to the options, before sending.
		'''

		# split the message in pieces if the option is set
		# we call partition even if opt_mul is disabled
		msg_parts, msg_lens = self.__partition(message)
		
		remaining = len(message)

		# send the partitioned or complete messages
		for k,m in enumerate(msg_parts):

			# encrypt if configured so
			if self.opt_enc:
				if len(self.enc_keys_en) == 0:
					self.log.no_encryption_keys()
				else:
					m = self.__encrypt(m)

			# add parity if configured so
			if self.opt_par: m = self.__addParity(m)

			remaining -= msg_lens[k]

			# Struct: [CID, ACK, EOM, REMAIN, LEN, CONTENT]
			msg_struct = self.pack(self.cid, ack, False, remaining, msg_lens[k], m)
			self.sock.sendto(msg_struct, (self.addr, self.port))
			
			# log the event
			self.log.sent(ack, remaining, msg_lens[k], m, 'UDP')
		
		return 


	def receive(self):
		'''
		Receive from server using UDP. Takes care of all the details:
		de/encryption, validity checks, multiparts...

		TODO: what do we do with sender_addr? check that it's the same?
		'''

		message = ''
		all_valid = True

		# reception loop
		while True:

			# receive and unpack a message (possibly a fragment if multipart)
			msg, sender_addr = self.sock.recvfrom(RECV_BYTES)
			cid, ack, eom, remain, length, content = self.unpack(msg)

			# last message does not have a parity bit
			if self.opt_par and not eom:
				content, valid = self.__checkParity(content, length)
				self.log.received_udp(content)
				if not valid: all_valid = False

			# last message is not encrypted (eom)
			if self.opt_enc and not eom:
				if len(self.enc_keys_de) == 0:
					self.log.no_decryption_keys()
				else:
					content = self.__decrypt(content)
			
			# invalid data --> ask for retransmission --> restart
			# we still have to wait 'til the end of multipart (remain = 0)
			if not all_valid and remain == 0:
				self.log.invalid_msg()
				self.send('Send again', ack=False)
				
				# basically start the receive function over
				message = ''
				all_valid = True
				continue

			else:
				# append the fragment to the message
				message += content

			# message received, go return it
			if remain == 0: break

		return (message, eom)


	def close(self):
		'''
		Simply close the socket.
		'''
		self.sock.close()
		return


	#--------------------------------------------------
	# 				  OPTION METHODS
	#--------------------------------------------------
	# This methods are used to enable/disable options
	# and pass required parameters for each feature.
	# -------------------------------------------------

	def enableEncryption(self, keys_en, keys_de):
		'''
		Enables encryption until keys run out.
		Apply new encryption and decryption keysets.
		Removes any remaining keys from the set.
		'''
		self.opt_enc = True

		# keysets are reversed so the first key is in the end of the
		# list – we can use list.pop() when using the keys
		self.enc_keys_en = keys_en[::-1]
		self.enc_keys_de = keys_de[::-1]

		return

	def enableMultipart(self, length):
		'''
		Enables multipart messages.
		Also sets a length for multipart message content.
		'''
		self.opt_mul = True
		self.mul_len = length

		return

	def enableParityCheck(self):
		'''
		Enables parity check for messages.
		Doesn't require any extra parameters.
		'''
		self.opt_par = True

		return


	#--------------------------------------------------
	# 				PRIVATE METHODS
	#--------------------------------------------------
	# These take care of nifty details of the class.
	# -------------------------------------------------

	# Encrypt & Decrypt

	def __encrypt(self, message):
		'''
		NOTE: Since the encryption method used is symmetrical, we could use
		the same method for both encryption and decryption.
		There are two reasons why these are still separately:
		1) I think it's simply clearer this way,
		2) Later it's easy to implement a new encryption algorithm.
		'''

		crypted = ''
		key = self.enc_keys_en.pop()
		for k,m in enumerate(message):
			crypted += chr( ord(m) ^ ord(key[k]) )

		return crypted

	def __decrypt(self, crypted):
		'''
		Decrypt a crypted message. See __encrypt() for details.
		'''
		message = ''
		key = self.enc_keys_de.pop()
		for k,m in enumerate(crypted):
			message += chr( ord(m) ^ ord(key[k]) )

		return message

	# Partition

	def __partition(self, message):
		'''
		Partition given message usinf @self.mul_len option.
		Returns a tuple containing a  list of message
		'fragments' and their lengths.
		'''

		parts, lengths = [], []

		# split the message into pieces and also save
		# their lengths before they're encrypted
		for i in range(0, len(message), self.mul_len):
			part = message[i:i+self.mul_len]
			parts.append(part)
			lengths.append( len(part) )

		return (parts, lengths)

	# Add & Check Parity

	def __addParity(self, message):
		'''
		Adds a parity bits to each character of the message.
		'''
		msg_par = ''
		for c in message:
			c = (ord(c) << 1)
			c += self.get_parity(c)
			msg_par += chr(c)

		return msg_par

	def __checkParity(self, msg_par, length):
		'''
		Checks parity from message and returns a tuple containing the message
		without parity and a boolean that tells if the message was valid.
		'''

		message = ''
		valid = True

		for c in msg_par:
			c = ord(c) 							# get numeric value of the character
			received_parity = c & 1 			# read the parity bit of a character
			c >>= 1 							# right shift by 1 bit
			actual_parity = self.get_parity(c) # calc the parity of the shifted character
			
			# compare to perceived parity bit
			if received_parity != actual_parity:
				valid = False
			
			# append the 'original' character to the message
			message += chr(c)

		return (message, valid)

	# Pack & Unpack

	def pack(self, cid, ack, eom, remain, length, content):
		'''
		Packs the data before sending. Uses struct library.

		Formatting
			Big Endian: 				!
			cid:		char[8] 		8s
			ack: 		bool 			?
			eom: 		bool 			?
			remain: 	unsigned short 	H
			length: 	unsigned short 	H
			content: 	char[128] 		128s
		'''
		return struct.pack(
			STRUCT_FORMAT,
			cid.encode(ENCODING),
			ack,
			eom,
			remain,
			length,
			content.encode(ENCODING)
		)

	def unpack(self, packet):
		'''
		Unpacks data from a struct packet.
		Check the method above for formatting details.
		'''
		cid, ack, eom, remain, length, content = struct.unpack(STRUCT_FORMAT, packet)

		# decode strings back from bytes format and return
		# also strip empty bytes if present (padding)
		return (
			cid.decode(ENCODING)[:8],
			ack,
			eom,
			remain,
			length,
			content.decode(ENCODING)[:length]
		)

	def get_parity(self, n):
		'''
		Get parity bit of given integer n.
		'''
		while n > 1:
			n = (n >> 1) ^ (n & 1)
		return n
