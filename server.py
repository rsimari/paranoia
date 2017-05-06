from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
import json


class PlayerConnection(Protocol):
	def __init__(self, port, init):
		self.port = port
		self.init_connection = init

	def connectionMade(self):
		print "player connection made"

	def dataReceived(self, data):
		print data
		self.init_connection.conn_controller.broadcast(data)

	def connectionLost(self, reason):
		# release port
		print "lost player connection"
		self.init_connection.available_ports.append(self.port)
		self.init_connection.conn_controller.removeConnection(self)
		self.transport.loseConnection()
		self.init_connection.conn_controller.stopListeningPort(self.port)

class PlayerConnectionFactory(Factory):
	def __init__(self, port, init):
		self.connection = PlayerConnection(port, init)

	def buildProtocol(self, addr):
		return self.connection

	def startedConnecting(self, n):
		pass

# class for handling all the players connections and their ports
class PlayerConnectionController(object):
	def __init__(self):
		self.conn_in_use = []
		self.ports = []

	def addConnection(self, conn):
		self.conn_in_use.append(conn)

	def removeConnection(self, conn):
		self.conn_in_use.remove(conn)

	def stopListeningPort(self, port_num):
		for port in self.ports:
			if port[1] == port_num:
				# frees port so another player can use it
				port[0].stopListening()

	def newListeningPort(self, port):
		self.ports.append(port)

	def broadcast(self, data):
		decoded_data = json.loads(data)
		for conn in self.conn_in_use:
			try:
				if conn.port != int(decoded_data["sender"]):
					conn.transport.write(data)
			except KeyError as e:
					print e

class InitConnection(Protocol):
	def __init__(self):
		self.available_ports = [40123, 41123, 42123, 41103, 42103]
		self.conn_controller = PlayerConnectionController()

	def connectionMade(self):
		print "new player found!"
		
		# check for more open ports
		if len(self.available_ports) < 1:
			print "no available ports"
			data = {"port": "-1"}
			self.transport.write(json.dumps(data))
			return 
		# assign whoever connected to this a port
		new_port = self.available_ports[len(self.available_ports) - 1]

		# start listening on the port
		new_conn = PlayerConnectionFactory(new_port, self)
		self.conn_controller.addConnection(new_conn.connection)
		port = reactor.listenTCP(new_port, new_conn)
		self.conn_controller.newListeningPort([port, new_port])

		# send port to player
		data = {"port": str(new_port)}
		self.transport.write(json.dumps(data))
		self.available_ports.pop()

	def connectionLost(self, reason):
		print "init connection lost"

	def dataReceived(self, data):
		print "dont send me data, I dont do anything"

class InitFactory(Factory):
	def __init__(self):
		self.connection = InitConnection()

	def buildProtocol(self, addr):
		return self.connection

class Server(object):
	def __init__(self):
		self.init_port = 40103

	def start(self):
		reactor.listenTCP(self.init_port, InitFactory())
		print "waiting for players on port", self.init_port
		reactor.run()

if __name__ == "__main__":
	server = Server()
	server.start()
