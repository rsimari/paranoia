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
from connections import GameConnection, GameConnectionFactory, InitConnection, InitConnectionFactory
from lasers import Laser, EnemyLaser

# class for entire pygame Gamespace
class GameSpace(object):
	def __init__(self, player, width, height):
		pygame.init()
		# set size of window for game
		self.size = self.width, self.height = width, height
		# set clear color
		self.black = 0, 0, 0
		self.screen = pygame.display.set_mode(self.size)

		self.game_objects = []
		self.player = player
		self.game_objects.append(self.player)
		self.enemies = {}
		self.game_started = 0

		### add text to screen ###
		self.draw_text = 1
		self.waiting_font = pygame.font.SysFont(None, 48)
		self.waiting_text = self.waiting_font.render('Waiting for more players...', True, (255,0,0), (0,0,0))
		self.waiting_textrect = self.waiting_text.get_rect()
		self.waiting_textrect.centerx = self.width / 2
		self.waiting_textrect.centery = self.height / 2
		#text_obj = {}

		### add health to screen ###
		self.health_font = pygame.font.SysFont(None, 25)
		self.health_text = self.health_font.render('Health: 100', True , (255,255,255), (0,0,0))
		self.health_rect = self.health_text.get_rect()
		self.health_rect.centerx = self.width / 2
		self.health_rect.centery = 20

		

	def update(self):
		# capture pygame events 
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN and self.game_started:
				self.player.move(event.key)
			elif event.type == pygame.MOUSEBUTTONDOWN and self.game_started:
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
	
			# see if game has enough players to start
			try:
				self.game_started = int(data["start"])
				self.draw_text = 0
				print "!!!!!!!!!", self.game_started
			except KeyError as e:
				pass

			# received state from server
			try:
				state = data["state"]
				print state
				for _id, pos in state.iteritems():
					if _id in self.enemies and _id is not self.player.connection.id:
						# moves enemy to position based on state sent from server
						self.enemies[_id].rect.center = pos
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

		# update health display
		health_rep = 'Health: ' + str(self.player.health)
		self.health_text = self.health_font.render(health_rep, True , (255,255,255), (0,0,0))


		# clear screen
		self.screen.fill(self.black)

		# draw all objects with new data/location
		for obj in self.game_objects:
			self.screen.blit(obj.image, obj.rect)

		if self.draw_text:
			self.screen.blit(self.waiting_text, self.waiting_textrect)

		self.screen.blit(self.health_text, self.health_rect)

		pygame.display.flip()


class Game(object):
	def __init__(self):
		self.init_port = 40103
		self.gs = None
		self.player = Player(self, self.gs)

	def start(self, width, height):
		self.gs = GameSpace(self.player, width, height)
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
