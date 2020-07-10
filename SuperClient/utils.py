def random_bytes(n):
	'''
	Return n random bytes using urandom file in Linux.
	For this, I found some help from stackoverflow.
	'''

	with open('/dev/urandom', 'rb') as file:
	 	return file.read(n)
