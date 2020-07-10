import sys
from SuperClient.Client import Client

if __name__ == '__main__':

	# boot up the Client with given arguments
	client = Client()
	client.start(sys.argv)

	# if client returned with an error, show the message
	if client.error:
		sys.exit(client.error_msg)