import pygame
import os
import json
import math
import sys

from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
from twisted.python import log
log.startLogging(sys.stdout)

# connection for sending data for multiplayer game
class GameConnection(Protocol):
	def __init__(self, _id, player):
		self.id = _id
		self.player = player
		self.game = player.game
		self.queue = []

	def connectionMade(self):
		print "connected with game server"
		if self.player.player_num == 1:
			self.joinGame([50, 50])
		elif self.player.player_num == 2:
			self.joinGame([self.game.gs.width - 50, self.game.gs.height - 50])
		elif self.player.player_num == 3:
			self.joinGame([self.game.gs.width - 50, 50])
		elif self.player.player_num == 3:
			self.joinGame([50, self.game.gs.height - 50])
		else: 
			self.joinGame([self.game.gs.width/2, self.game.gs.height/2])

		self.game.start()

	def joinGame(self, rect):
		data = {"sender": str(self.id), "init": rect}
		self.transport.write(json.dumps(data) + "____")

	def dataReceived(self, data):
		print data
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
	def __init__(self, _id, player):
		self.connection = GameConnection(_id, player)

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
		self.player.player_num = data["player_num"]
		conn = GameConnectionFactory(data["port"], self.player)
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
	def __init__(self, game, gs, pos = (50, 50)):
		pygame.sprite.Sprite.__init__(self)
		self.connection = None
		self.gs = gs
		self.game = game
		self.health = 100
		self.player_num
		self.rect = pygame.Rect(pos, (100, 100))
		self.rect.center = pos
		self.image = pygame.image.load('deathstar.png')
		self.lasers = []

	def sendData(self, data):
		if self.connection != None:
			self.connection.send(data + "____")

	def move(self, key):

		data = {"sender": str(self.connection.id)}

		if key == pygame.K_d:
			self.rect.centerx += 5
			data["position"] = [self.rect.centerx, self.rect.centery]
			self.sendData(json.dumps(data))
		elif key == pygame.K_a:
			self.rect.centerx -= 5
			data["position"] = [self.rect.centerx, self.rect.centery]
			self.sendData(json.dumps(data))
		elif key == pygame.K_w:
			self.rect.centery -= 5
			data["position"] = [self.rect.centerx, self.rect.centery]
			self.sendData(json.dumps(data))
		elif key == pygame.K_s:
			self.rect.centery += 5
			data["position"] = [self.rect.centerx, self.rect.centery]
			self.sendData(json.dumps(data))

	def fire(self, x, y):
		print "firing laser..."
		mouse_pos = pygame.mouse.get_pos()
		opp = mouse_pos[1] - self.rect.centery
		adj = mouse_pos[0] - self.rect.centerx
		angle = math.atan2(opp, adj)
		dx = math.cos(angle)
		dy = math.sin(angle)

		data = {"sender": str(self.connection.id), "laser": [x, y, dx, dy]}
		self.sendData(json.dumps(data))

		laser = Laser(x, y, dx, dy, self.gs)
		self.lasers.append(laser)
		return laser

	def tick(self):
		if self.health <= 0:
			# remove player from game
			print "DEAD"
			self.gs.game_objects.remove(self)
			data = {"sender": str(self.connection.id), "del": str(self.connection.id)}
			self.sendData(json.dumps(data))

# other player's sprite
class Enemy(pygame.sprite.Sprite):
	def __init__(self,  _id, rect = [50, 50]):
		pygame.sprite.Sprite.__init__(self)
		self.rect = pygame.Rect((rect[0], rect[1]), (100, 100))
		self.rect.center = tuple(rect)
		self.image = pygame.image.load('deathstar.png')
		self.id = _id

	def move(self, data):
		try:
			pos = data["position"]
			self.rect.centerx = pos[0]
			self.rect.centery = pos[1]
		except KeyError as e:
			pass

	def tick(self):
		pass

# laser objects that get shot player
class Laser(pygame.sprite.Sprite):
	def __init__(self, x, y, dx, dy, gs):
		pygame.sprite.Sprite.__init__(self)
		self.rect = pygame.Rect((x, y), (10, 10))

		self.image = pygame.image.load('laser.png')

		self.speed = 10
		self.gs = gs
		self.dx = dx
		self.dy = dy

	def tick(self):
		self.rect.centerx += (self.speed * self.dx)
		self.rect.centery += (self.speed * self.dy)
		# detect collision
		for _id, e in self.gs.enemies.iteritems():
			if self.rect.colliderect(e.rect):
				self.gs.game_objects.remove(self)

class EnemyLaser(pygame.sprite.Sprite):
	def __init__(self, x, y, dx, dy, player, gs):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load('laser.png')
		self.rect = pygame.Rect((x, y), (10, 10))

		self.target = player
		self.gs = gs
		self.speed = 10
		self.dx = dx
		self.dy = dy

	def tick(self):
		self.rect.centerx += (self.speed * self.dx)
		self.rect.centery += (self.speed * self.dy)

		# detect collision
		if self.rect.colliderect(self.target.rect):
			self.target.health -= 10
			# remove laser from game
			self.gs.game_objects.remove(self)


# class for entire pygame Gamespace
class GameSpace(object):
	def __init__(self, player):
		pygame.init()
		# set size of window for game
		self.size = self.width, self.height = 800, 500
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
			elif event.type == pygame.MOUSEBUTTONDOWN:
				# player fires laser
				laser = self.player.fire(self.player.rect.centerx, self.player.rect.centery)
				self.game_objects.append(laser)

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
			try:
				laser_data = data["laser"]
				print data
				laser = EnemyLaser(laser_data[0], laser_data[1], laser_data[2], laser_data[3], self.player, self)
				self.game_objects.append(laser)
				print laser
			except KeyError as e:
				pass


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
		self.gs = None
		self.player = Player(self, self.gs)

	def start(self):
		self.gs = GameSpace(self.player)
		self.player.gs = self.gs
		pygame.key.set_repeat(1, 10)
		lc = LoopingCall(self.gs.update)
		lc.start(0.0166)

	def connect(self):
		reactor.connectTCP("localhost", self.init_port, InitConnectionFactory(self.player))
		# reactor.connectTCP("ash.campus.nd.edu", self.init_port, InitConnectionFactory(self.player))


if __name__ == "__main__":
	game = Game()
	game.connect()

	reactor.run()
