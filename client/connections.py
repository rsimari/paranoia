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

from players import Player, Enemy
from lasers import Laser, EnemyLaser


# connection for sending data for multiplayer game
class GameConnection(Protocol):
	def __init__(self, _id, player):
		self.id = _id
		self.player = player
		self.game = player.game
		self.queue = []

	def connectionMade(self):
		print "connected with game server"
		width = 800
		height = 500
		print "PLAYER: ", self.player.player_num

		if self.player.player_num == "1":
			self.player.rect.center = (50, 50)
			self.joinGame([50, 50])
		elif self.player.player_num == "2":
			self.player.rect.center = (width - 50, height - 50)
			self.joinGame([width - 50, height - 50])
		elif self.player.player_num == "3":
			self.player.rect.center = (width - 50, 50)
			self.joinGame([width - 50, 50])
		elif self.player.player_num == "4":
			self.player.rect.center = (50, height - 50)
			self.joinGame([50, height - 50])
		else: 
			self.player.rect.center = (width/2, height/2)
			self.joinGame([width/2, height/2])

		self.game.start(width, height)


	def joinGame(self, rect):
		data = {"sender": str(self.id), "init": rect}
		self.transport.write(json.dumps(data) + "____")

	def dataReceived(self, data):
		# print data
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