import pygame
import os
import json

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue

# connection for sending data for multiplayer game
class GameConnection(Protocol):
	def __init__(self, _id, game):
		self.id = _id
		self.game = game
		self.queue = []

	def connectionMade(self):
		print "connected with game server"
		self.joinGame([100,100])
		self.game.start()

	def joinGame(self, rect):
		data = {"sender": str(self.id), "init": rect}
		self.transport.write(json.dumps(data))

	def dataReceived(self, data):
		print data
		for d in data.split("____")[:-1]:
			print json.loads(d)
			self.queue.insert(0, json.loads(d))

	def send(self, data):
		self.transport.write(data)

class GameConnectionFactory(Factory):
	def __init__(self, _id, game):
		self.connection = GameConnection(_id, game)

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
		print data
		data = json.loads(data)
		# check if there was an open port to give me
		try:
			if data["port"] == "-1":
				print "server is at max connections"
				return 
		except KeyError as e:
			pass
		# receives port to connect to and connects to that port for game data
		conn = GameConnectionFactory(data["port"], self.player.game)
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

	def clientConnectionFailed(self, connector, reason):
		print "could not connect to the server"
		# quit program
		os._exit(0)

# the main players sprite
class Player(pygame.sprite.Sprite):
	def __init__(self, game):
		self.connection = None
		self.game = game
		self.rect = pygame.Rect((0,0), (100, 100))
		# charImage = pygame.image.load('/home/scratch/paradigms/deathstar/deathstar.png')
		self.image = pygame.image.load('deathstar.png')
		# charImage = pygame.transform.scale(charImage, self.rect.size)
		# self.image = charImage.convert()
		self.id = 3

	def sendData(self, data):
		if self.connection != None:
			self.connection.send(data)

	def move(self, key):
		self.rect = list(self.rect)

		data = {"sender": str(self.connection.id)}
		if key == pygame.K_d:
			self.rect[0] += 5
			data["position"] = self.rect
			self.sendData(json.dumps(data))
		elif key == pygame.K_a:
			self.rect[0] -= 5
			data["position"] = self.rect
			self.sendData(json.dumps(data))
		elif key == pygame.K_w:
			self.rect[1] -= 5
			data["position"] = self.rect
			self.sendData(json.dumps(data))
		elif key == pygame.K_s:
			self.rect[1] += 5
			data["position"] = self.rect
			self.sendData(json.dumps(data))

		self.rect = tuple(self.rect)

	def tick(self):
		pass

# other player's sprite
class Enemy(pygame.sprite.Sprite):
	def __init__(self,  _id, rect = [0, 0]):
		self.rect = pygame.Rect(tuple(rect), (100, 100))
		# charImage = pygame.image.load('/home/scratch/paradigms/deathstar/deathstar.png')
		self.image = pygame.image.load('deathstar.png')
		self.id = _id

	def move(self, data):
		try:
			pos = data["position"]
			self.rect = tuple(pos)
		except KeyError as e:
			pass


	def tick(self, data):
		print "tick"	


# class for entire pygame Gamespace
class GameSpace(object):
	def __init__(self, player):
		pygame.init()
		# set size of window for game
		self.size = self.width, self.height = 640, 480
		# set clear color
		self.black = 0, 0, 0
		self.screen = pygame.display.set_mode(self.size)

		self.game_objects = []
		self.player = player
		self.game_objects.append(self.player)
		self.enemies = {}

	def update(self):
		# capture pygame events 
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				self.player.move(event.key)

		# get data from server
		for data in list(reversed(self.player.connection.queue)):
			data = json.loads(data)
			# add enemy in here if one joins
			_id = data["sender"]
			try:
				rect = data["init"]
				e = Enemy( _id, rect)
				self.game_objects.append(e)
				self.enemies[_id] = e
			except KeyError as e:
				pass

			# update enemies
			try:
				self.enemies[_id].move(data)
			except KeyError as e:
				pass

			# self.enemy.move(data)
			# print self.player.connection.queue[0]
			# print data
			self.player.connection.queue.pop()

		# call tick() on each object that updates their data/location
		for obj in self.game_objects:
			pass
			# obj.tick()

		# clear screen
		self.screen.fill(self.black)

		# draw all objects with new data/location
		for obj in self.game_objects:
			if obj.id == 2:
				print "hi"
			self.screen.blit(obj.image, obj.rect)

		pygame.display.flip()

class Game(object):
	def __init__(self):
		self.init_port = 40103
		self.player = Player(self)

	def start(self):
		self.gs = GameSpace(self.player)
		lc = LoopingCall(self.gs.update)
		lc.start(0.0166)

	def connect(self):
		reactor.connectTCP("ash.campus.nd.edu", self.init_port, InitConnectionFactory(self.player))


if __name__ == "__main__":
	game = Game()
	game.connect()

	reactor.run()
