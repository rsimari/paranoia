import pygame
import os
import json

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor


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

class GameConnectionFactory(Factory):
	def __init__(self, _id):
		self.connection = GameConnection(_id)

	def buildProtocol(self, addr):
		return self.connection

	def startedConnecting(self, n):
		pass

	def clientConnectionLost(self, connector, reason):
		pass


class InitConnection(Protocol):
	def __init__(self):
		pass

	def connectionMade(self):
		print "established connection with server"

	def dataReceived(self, data):
		data = json.loads(data)
		# check if there was an open port to give me
		if data["port"] == "-1":
			print "server is at max connections"
			return 
		# receives port to connect to and connects to that port for game data
		reactor.connectTCP("ash.campus.nd.edu", int(data["port"]), GameConnectionFactory(data["port"]))

class InitConnectionFactory(Factory):
	def __init__(self):
		self.connection = InitConnection()

	def buildProtocol(self, addr):
		return self.connection

	def startedConnecting(self, n):
		print "connecting..."

	def clientConnectionLost(self, connector, reason):
		print "disconnected from game server"
		self.connection.transport.loseConnection()
		os._exit(0)

# class for entire pygame Gamespace
class GameSpace(object):
	def __init__(self):
		pygame.init()
		# set size of window for game
		self.size = self.width, self.height = 640, 480
		# set clear color
		self.black = 0, 0, 0
		self.screen = pygame.display.set_mode(self.size)

		self.clock = pygame.time.Clock()
		self.game_objects = []

		while(1):
			# tick 60 times per second
			self.clock.tick(60)

			# capture pygame events 
			for event in pygame.event.get():
				pass

			# send data to server here?

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

	def start(self):
		gs = GameSpace()
		gs.main()

	def connect(self):
		reactor.connectTCP("ash.campus.nd.edu", self.init_port, InitConnectionFactory())


if __name__ == "__main__":
	game = Game()
	game.connect()
	game.start()
	
	reactor.run()
