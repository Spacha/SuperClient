'''
UI.py
	This file contains all of the "UI" components. The UI actually consists of
	characters printed on console. And some imagination.
'''

# ANSI formatting
class txt:
	purple = '\033[95m' 		# purple
	blue = '\033[94m' 			# blue
	green = '\033[92m' 			# green
	yellow = '\033[93m' 		# yellow
	red = '\033[91m' 			# red
	grey = '\033[90m' 			# grey

	# Special
	bold = '\033[1m'
	underline = '\033[4m'
	endc = '\033[0m'

	def __init__(self, ansi=True):
		'''
		Sorry, this is just a quick fix.
		If ansi is disabled, replace all with empty strings...
		'''
		if not ansi:
			self.purple, self.blue, self.green, self.yellow, self.red, self.grey, self.bold, self.underline, self.endc = '', '', '', '', '', '', '', '', ''


class UI:
	# these don't really belong here...
	STR_DESCRIPTION = "This is a simple TCP & UDP client application made as part of 'Fundamentals of Internet' course. The assignment itself doesn't require anything super special but as I had to spend wappu eristyksissä, I had nothing better to do (I drank 28 beers, though). That said, I apologize if the program fails because all the over-engineering or ASCII craziness."
	CHANGELOG = [
		'1.04: Updated description 9 -> 28 beers',
		'1.03: Updated description 4 -> 9 beers',
		'1.02: Updated description 2 -> 4 beers',
		'1.00: First stable version',
	]
	# use RLE or something :D
	LOGO = [
		" _____                         _____   _             _  ",
		"/  ___|                       /  __ \\ (_)           | | ",
		"\\ `--. _   _ _ __   ___ _ __  | /  \\\\/ |_  ___ _ __ | |_",
		" `--. \\ | | | '_ \\ / _ \\ '__| | |   | | |/ _ \\ '_ \\| __|",
		"/\\__/ / |_| | |_) |  __/ |    | \\__/\\ | |  __/ | | | |_ ",
		"\\____/ \\__,_| .__/ \\___|_|     \\____/_|_|\\___|_| |_|\\__|",
		"            | | by Spacha                               ",
		"            |_|                                         "
	]
	frame_width = 68
	ansi = False

	# modes
	mode_border = False
	numbers_curr = 1

	# elements
	ELEM_HLINE =     '-'
	ELEM_HLINE_END = '+'
	ELEM_VLINE =     '|'

	txt = None

	def __init__(self, ansi):
		self.ansi = ansi
		self.txt = txt(ansi)
		return

	def enableANSI(self):
		self.ansi = True
		self.txt = txt(True)
	

	#--------------------------------------------------
	# 			    HIGH-LEVEL UI METHODS
	#--------------------------------------------------
	# These methods use primitive methods to show more
	# complicated UI 'components'
	#--------------------------------------------------

	def logo(self):
		'''
		Print a NICE and RESPONSIVE ASCII art that probably doesn't work on
		other machines! But hey, it's not like I didn't try!
		Ei for Effort, right?
		'''
		self.horLine(noPadding=True)
		self.emptyLine()

		for lline in self.LOGO:
			self.text(lline, center=True, wrap=False, bold=True, noSpace=True)
		return

		self.emptyLine()

	def changelog(self):
		'''
		Show very relevant changelog!
		'''
		self.emptyLine()
		self.text("Changelog:", clr='grey', ul=True, leftPad=3)
		for log in self.CHANGELOG:
			self.text(log, clr='grey', leftPad=4)
		return
	
	def description(self):
		'''
		Short description of the application. I'm so funny, am I not.
		'''
		self.text(self.STR_DESCRIPTION, center=True, clr='grey')
		return

	def info(self, text):
		'''
		'''
		self.text("[INFO] ", bold=True, clr='green', newLine=False)
		self.text(text, bold=True, leftPad=0)

	def warning(self, text):
		'''
		'''
		self.text("[WARN] \t", bold=False, clr='yellow', newLine=False)
		self.text(text, bold=False)

	def error(self, text, noPrint=False):
		'''
		'''
		line_buffer = ''
		line_buffer += self.text("[ERRO] \t", bold=False, clr='red', newLine=False, noPrint=noPrint, wrap=False)
		line_buffer += self.text(text, bold=False, noPrint=noPrint, wrap=False)

		# if noPrint, return as a string
		if noPrint:
			return line_buffer
		return

	def info_ok(self, text):
		'''
		'''
		self.text("\t» " + text, clr='green', newLine=False, leftPad=7, wrap=False)
		self.emptyLine()

	def numbered(self, text):
		'''
		'''
		self.text(f" {self.numbers_curr}. {text}", leftPad=7, wrap=False)
		self.numbers_curr += 1

	def indented(self, bullet='*', text=''):
		'''
		'''
		self.text(f"    {bullet} ", newLine=False, leftPad=7, wrap=False)
		self.text(text, clr='grey', linePrefix="       \t      ")


	#--------------------------------------------------
	# 			    PRIMITIVE UI METHODS
	#--------------------------------------------------
	# Methods for assembling primitive UI elements like
	# text, borders and so on.
	#--------------------------------------------------

	def text(self, text='', clr='', bold=False, ul=False, center=False, wrap=True, leftPad=-1, newLine=True, noPrint=False, linePrefix = '', noSpace=False):
		'''
		Prints a nicely formatted text to the console.
		@text 			The text to be printed.
		@clr 			Color of the text. See colors in top of this file.
		@center 		Center the text to @self.frame_width.
		@wrap 			Wrap long text to multiple lines.
		@leftPad 		Left padding. Default is 2.
		@newLine 		Newline after text. Default is True.
		@noPrint 		Don'r print the text but return as string. Default is False.
		@linePrefix 	Add a prefix to all lines (hax to get indented mline text)
		@noSpace 		Don't convert underscores to spaces.

		To make multiple spaces, use underscore ('_').
		This also prevents word wrap.
		'''

		fw = self.frame_width
		
		if noPrint:
			line_buffer = ''

		if leftPad == -1:
			if self.mode_border:
				leftPad = 2 		# default padding for border mode
			else:
				leftPad = 0


		# first of all, split the text in lines if necessary
		if wrap:
			lines, line_lens = self.wrapText(text)
		else:
			lines, line_lens = [text], [len(text)]

		for lnum,line in enumerate(lines):
			# underscore --> space
			if not noSpace:
				if '_' in line:
					line = line.replace('_', ' ')
			line_len = line_lens[lnum]


			# Text Decoration

			if bold:
				line = f"{self.txt.bold}{line}{self.txt.endc}"
			if ul:
				line = f"{self.txt.underline}{line}{self.txt.endc}"


			# Colors

			# luckily python has switch-case...
			# COLORS, tho! I'm drunk, send help.
			if clr:
				if clr == 'purple':
					line = f"{self.txt.purple}{line}{self.txt.endc}"
				elif clr == 'blue':
					line = f"{self.txt.blue}{line}{self.txt.endc}"
				elif clr == 'green':
					line = f"{self.txt.green}{line}{self.txt.endc}"
				elif clr == 'yellow':
					line = f"{self.txt.yellow}{line}{self.txt.endc}"
				elif clr == 'red':
					line = f"{self.txt.red}{line}{self.txt.endc}"
				elif clr == 'grey':
					line = f"{self.txt.grey}{line}{self.txt.endc}"


			# Padding

			# frame mode is required to center a line (pad = padding)
			if self.mode_border:
				pad = fw - line_len - 2 		# -2 because of borders in both ends

				# if centered: use integer division
				# if default (left padding), just padding of 2 (or user defined)
				leftPad = pad // 2 if center else leftPad
				rightPad = pad - leftPad
					
				# print(leftPad, line_len, rightPad)
				line = ''.join([' ' * leftPad]) + line + ''.join([' ' * rightPad])
			else:
				line = ''.join([' ' * leftPad]) + line

			# Vertical Borders

			if self.mode_border:
				# bolded borders
				line = f"{self.txt.bold}{self.ELEM_VLINE}{self.txt.endc}{line}{self.txt.bold}{self.ELEM_VLINE}{self.txt.endc}"

			# add a line prefix if there's one
			if lnum > 0:
				line = linePrefix + line
			

			# Aaand... Action!
			if noPrint:
				# TODO: add newlines
				line_buffer += line
			else:
				if newLine:
					print(line)
				else:
					print(line, end='')

		if noPrint:
			return line_buffer
		return

	def borderStart(self):
		'''
		Start a (vertical) bordering mode. All texts before calling
		@self.borderEnd() will have borders. Exception to this is
		horizontal line which doesn't care about bordering mode.
		'''
		self.mode_border = True
		return

	def borderEnd(self):
		'''
		Ends a border. See @self.borderStart()
		'''
		self.mode_border = False
		return

	def resetNumbering(self):
		'''
		'''
		self.numbers_curr = 1
		return

	def horLine(self, noPadding=False, noPrint=False):
		'''
		Prints a horizontal line. We need to disable bordermode momentarily.
		@noPadding 	Don't print empty lines before and after. Default is False.
		'''
		line = ''.join([ self.ELEM_HLINE * (self.frame_width - 2) ])
		bmode = self.mode_border

		if not noPadding:
			self.emptyLine()

		# add 'ends' or 'corners' to the border
		if bmode: self.borderEnd()
		line_buff = self.text(self.ELEM_HLINE_END + line + self.ELEM_HLINE_END, bold=True, wrap=False, noPrint=noPrint)
		if bmode: self.borderStart()

		if not noPadding:
			self.emptyLine()

		if noPrint:
			return line_buff
		return

	def emptyLine(self):
		'''
		This is purely cosmetic.
		'''
		self.text()


	#--------------------------------------------------
	# 				 UTILITY METHODS
	#--------------------------------------------------
	# Various helper methods for wrapping common tasks.
	#--------------------------------------------------

	def wrapText(self, text):
		'''
		Divides a long line of text into multiple lines by spaces.
		Similar to __partition() method in UDPConnection class!

		NOTE: This is not by any meanas the most efficient way but it works!
		'''

		# first, split the test into individual words
		words = text.split(' ')

		lines = ['']
		lengths = [0]
		curr_line = 0

		for word in words:
			word_len = len(word)+1

			# first word of first line, this is annoying...
			if curr_line == 0 and lengths[0] == 0:
				word_len -= 1

			# overflow --> new line
			if lengths[curr_line] + word_len >= (self.frame_width - 4):
				curr_line += 1
				lines.append('')
				lengths.append(0)
				word_len -= 1

			# add word to the line
			if len(lines[curr_line]) == 0:
				lines[curr_line] += word
			else:
				lines[curr_line] += ' ' + word

			# update the length
			lengths[curr_line] += word_len

		return (lines, lengths)
