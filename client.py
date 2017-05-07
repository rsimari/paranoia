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
		self.joinGame([0,0])
		self.game.start()

	def joinGame(self, rect):
		data = {"sender": str(self.id), "init": rect}
		self.transport.write(json.dumps(data) + "____")

	def dataReceived(self, data):
		for d in data.split("____")[:-1]:
			d = json.loads(d)
			try:
				if d["sender"] != self.id:
					self.queue.insert(0, d)
			except KeyError as e:
				self.queue.insert(0, d)


	def send(self, data):
		self.transport.write(data + "____")

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
		# reactor.connectTCP("ash.campus.nd.edu", int(data["port"]), conn)
		reactor.connectTCP("localhost", int(data["port"]), conn)

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
	def __init__(self, game, pos = (0, 0)):
		pygame.sprite.Sprite.__init__(self)
		self.connection = None
		self.game = game
		self.rect = pygame.Rect(pos, (100, 100))
		self.image = pygame.image.load('deathstar.png')
		self.lasers = []

	def sendData(self, data):
		if self.connection != None:
			self.connection.send(data + "____")

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

	def fire(self, pos, dx, dy):
		print "firing laser..."
		data = {"sender": str(self.connection.id), "laser": [pos[0], pos[1], dx, dy]}
		self.sendData(json.dumps(data))

		laser = Laser(pos[:2], dx, dy)
		self.lasers.append(laser)
		return laser


	def tick(self):
		pass

# other player's sprite
class Enemy(pygame.sprite.Sprite):
	def __init__(self,  _id, rect = [0, 0]):
		pygame.sprite.Sprite.__init__(self)
		self.rect = pygame.Rect(tuple(rect[:2]), (100, 100))
		self.image = pygame.image.load('deathstar.png')
		self.id = _id

	def move(self, data):
		try:
			pos = data["position"]
			self.rect = tuple(pos)
		except KeyError as e:
			pass

	def tick(self):
		pass

# laser objects that get shot from players
class Laser(pygame.sprite.Sprite):
	def __init__(self, rect, dx, dy):
		pygame.sprite.Sprite.__init__(self)
		self.rect = pygame.Rect(tuple(rect[:2]), (10, 10))
		self.image = pygame.image.load('deathstar.png')

		self.dx = dx
		self.dy = dy

	def tick(self):
		self.rect[0] += dx
		self.rect[1] += dy

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
				if event.key == pygame.K_SPACE:
					# player fires laser
					# (x, y), dx, dy
					laser = self.player.fire((0,0), 1, 1)
					self.game_objects.append(laser)
				else:
					self.player.move(event.key)

		# get data from server
		for data in list(reversed(self.player.connection.queue)):
			print data
			# update enemies
			try:
				_id = data['sender']
				self.enemies[_id].move(data)
			except Exception as e:
				pass

			# see if any player left from game and remove them from our screen
			try:
				_id = data["del"]
				e = self.enemies[str(_id)]
				self.game_objects.remove(e)
				del self.enemies[str(_id)]
			except KeyError as e:
				pass

			# received state from server
			try:
				state = data["state"]
				print state
				for _id, pos in state.iteritems():
					if _id in self.enemies and _id is not self.player.connection.id:
						# moves enemy to position based on state sent from server
						self.enemies[_id].rect = pos
					elif _id != self.player.connection.id:
						e = Enemy(_id, pos)
						self.enemies[_id] = e
						self.game_objects.append(e)
			except KeyError as e:
				pass
			self.player.connection.queue.pop()

			# receive laser fire from server


		# call tick() on each object that updates their data/location
		for obj in self.game_objects:
			obj.tick()

		# clear screen
		self.screen.fill(self.black)

		# draw all objects with new data/location
		for obj in self.game_objects:
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
		reactor.connectTCP("localhost", self.init_port, InitConnectionFactory(self.player))
		# reactor.connectTCP("ash.campus.nd.edu", self.init_port, InitConnectionFactory(self.player))


if __name__ == "__main__":
	game = Game()
	game.connect()

	reactor.run()
