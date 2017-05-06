import pygame
import os
import json

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

# connection for sending data for multiplayer game
class GameConnection(Protocol):
	def __init__(self, _id):
		self.id = _id
		pass

	def connectionMade(self):
		print "connected with game server"
		data = {"sender": self.id}
		self.transport.write(json.dumps(data))

	def dataReceived(self, data):
		print json.loads(data)

	def send(self, data):
		self.transport.write(data)

class GameConnectionFactory(Factory):
	def __init__(self, _id):
		self.connection = GameConnection(_id)

	def buildProtocol(self, addr):
		return self.connection

	def startedConnecting(self, n):
		pass

	def clientConnectionLost(self, connector, reason):
		pass

# connection for initial connect to server
class InitConnection(Protocol):
	def __init__(self, player):
		self.player = player

	def connectionMade(self):
		print "established connection with server"

	def dataReceived(self, data):
		data = json.loads(data)
		# check if there was an open port to give me
		if data["port"] == "-1":
			print "server is at max connections"
			return 
		# receives port to connect to and connects to that port for game data
		conn = GameConnectionFactory(data["port"])
		self.player.connection = conn.connection
		reactor.connectTCP("ash.campus.nd.edu", int(data["port"]), conn)

class InitConnectionFactory(Factory):
	def __init__(self, player):
		self.connection = InitConnection(player)

	def buildProtocol(self, addr):
		return self.connection

	def startedConnecting(self, n):
		print "connecting..."

	def clientConnectionLost(self, connector, reason):
		print "disconnected from game server"
		self.connection.transport.loseConnection()
		# quit program
		os._exit(0)


class Player(object):
	def __init__(self):
		self.connection = None

	def sendData(self, data):
		print "sending..."
		if self.connection != None:
			self.connection.send(data)

# class for entire pygame Gamespace
class GameSpace(object):
	def __init__(self, player):
		pygame.init()
		# set size of window for game
		self.size = self.width, self.height = 640, 480
		# set clear color
		self.black = 0, 0, 0
		self.screen = pygame.display.set_mode(self.size)

		self.clock = pygame.time.Clock()

		self.game_objects = []
		self.player = player

	def update(self):
		print "here" 
		# capture pygame events 
		for event in pygame.event.get():
			pass

		# send data to server here?
		self.player.sendData('{"sender": "' + str(self.player.id) + '"}')

		# call tick() on each object that updates their data/location
		for obj in self.game_objects:
			pass
			# obj.tick()

		# clear screen
		self.screen.fill(self.black)

		# draw all objects with new data/location
		for obj in self.game_objects:
			pass
			# self.screen.blit(obj.image, obj.rect)

		pygame.display.flip()

class Game(object):
	def __init__(self):
		self.init_port = 40103
		self.player = Player()

	def start(self):
		self.gs = GameSpace(self.player)
		print "hi"
		lc = LoopingCall(self.gs.update)
		lc.start(0.0166)

	def connect(self):
		reactor.connectTCP("ash.campus.nd.edu", self.init_port, InitConnectionFactory(self.player))


if __name__ == "__main__":
	game = Game()

	game.connect()
	game.start()

	reactor.run()
