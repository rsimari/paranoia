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
		print "original: ", data
		data_set = data.split("____")
		print data_set
		for data in data_set[:-1]:
			if len(data) > 1:
				data = json.loads(data)
				_id = data["sender"]
				try:
					# new player
					pos = data["init"]
					self.init_connection.conn_controller.addPlayer(_id, pos)
					self.init_connection.conn_controller.broadcastState()
				except KeyError as e:
					pass	

				try:
					# player got updated
					pos = data["position"]
					self.init_connection.conn_controller.updatePlayer(_id, pos)
				except KeyError as e:
					pass
				# broadcasts changes to clients	
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
		self.player_pos = {}
		self.state = {"state": self.player_pos}

	def addConnection(self, conn):
		print "added"
		self.conn_in_use.append(conn)

	def removeConnection(self, conn):
		self.conn_in_use.remove(conn)

	def addPlayer(self, port, position):
		self.player_pos[port] = position

	def updatePlayer(self, port, position):
		self.player_pos[port] = position

	def removePlayer(self, port):
		del self.player_pos[port]

	def stopListeningPort(self, port_num):
		for port in self.ports:
			if port[1] == port_num:
				# frees port so another player can use it
				port[0].stopListening()

	def newListeningPort(self, port):
		self.ports.append(port)

	def broadcast(self, decoded_data):
			for conn in self.conn_in_use:
				try:
					if conn.port != int(decoded_data["sender"]):
						try:
							conn.transport.write(json.dumps(decoded_data) + "____")
						except AttributeError as e:
							print e
				except KeyError as e:
					print e

	def broadcastState(self):
			print "broadcast state..."
			for conn in self.conn_in_use:
				conn.transport.write(json.dumps(self.state) + "____")

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
