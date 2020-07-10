'''
	This class takes care of saving/printing detailed
	information of what's happening during execution.
'''
class Log:
	ui = None
	verbose = False

	def __init__(self, ui, verbose):
		self.verbose = verbose
		self.ui = ui

		if not self.verbose: return

		self.ui.text("Verbose mode active.")

	def warning(self, text):
		if not self.verbose: return

		self.ui.emptyLine()
		self.ui.text('[WARN] ', clr='yellow', newLine=False)
		self.ui.text(text)
		self.ui.emptyLine()

	def debug(self, text):
		if not self.verbose: return

		self.ui.text('\n[DEBG] ', clr='grey', bold=True, newLine=False)
		self.ui.text(text)


	#--------------------------------------------------
	# 				   USER METHODS
	#--------------------------------------------------
	# User methods that have one purpose only: to be
	# used in a certain situation, it's up to the user.
	# -------------------------------------------------
	
	def received_tcp(self, messages):
		if not self.verbose: return

		self.debug('TCP message received: ')
		for m in messages:
			self.ui.text("%r" % m, wrap=False, leftPad=8, linePrefix='        ')

	def received_udp(self, message):
		if not self.verbose: return

		self.debug('UDP message received: ')
		self.ui.text("%r" % message, wrap=False, leftPad=8, linePrefix='        ')

	def sent(self, ack, remaining, length, msg, protocol):
		if not self.verbose: return

		self.debug(protocol + ' message sent: ')
		self.ui.text("ACK: {}, remaining: {}, len: {}, content: {}".format(ack, remaining, length, msg), wrap=False, leftPad=8, linePrefix='        ')


	def invalid_msg(self):
		if not self.verbose: return
		
		self.ui.text('Invalid message. Asking for retransmission.\n')

	def no_encryption_keys(self):
		if not self.verbose: return

		self.warning("No encryption keys. Sending as plain text.")

	def no_decryption_keys(self):
		if not self.verbose: return

		self.warning("No decryption keys. Received as plain text.")
