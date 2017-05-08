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

from lasers import Laser, EnemyLaser


class Player(pygame.sprite.Sprite):
	def __init__(self, game, gs, pos = (50, 50)):
		pygame.sprite.Sprite.__init__(self)
		self.connection = None
		self.gs = gs
		self.game = game
		self.health = 100
		self.player_num = 0
		self.rect = pygame.Rect(pos, (75, 75))
		self.rect.center = pos
		self.image = pygame.image.load('jet.png')
		self.image = pygame.transform.scale(self.image, self.rect.size)
		self.lasers = []

		self.originalImage = self.image
		self.originalRect = self.rect

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
		angle = self.get_angle()
		dx = math.cos(angle)
		dy = math.sin(angle)

		data = {"sender": str(self.connection.id), "laser": [x, y, dx, dy]}
		self.sendData(json.dumps(data))

		laser = Laser(x, y, dx, dy, self.gs)
		self.lasers.append(laser)
		return laser

	def get_angle(self):
		mouse_pos = pygame.mouse.get_pos()
		opp = mouse_pos[1] - self.rect.centery
		adj = mouse_pos[0] - self.rect.centerx
		angle = math.atan2(opp, adj)
	
		return angle


	def tick(self):
		if self.health <= 0:
			# remove player from game
			print "DEAD"
			self.gs.game_objects.remove(self)
			data = {"sender": str(self.connection.id), "del": str(self.connection.id)}
			self.sendData(json.dumps(data))
			# end game
			self.health = 0
			self.gs.game_started = 0
			self.gs.game_ended = 1

		angle = -math.degrees(self.get_angle())
		#print angle
		rot_image = pygame.transform.rotate(self.originalImage, angle)
		rot_rect = self.originalRect.copy()
		rot_rect.center = rot_image.get_rect().center
		rot_image = rot_image.subsurface(rot_rect).copy()
		self.image = rot_image
		rot_data = {"angle":str(angle), "sender": str(self.connection.id)}
		self.sendData(json.dumps(rot_data))


class Enemy(pygame.sprite.Sprite):
	def __init__(self,  _id, rect = [50, 50]):
		pygame.sprite.Sprite.__init__(self)
		self.rect = pygame.Rect((rect[0], rect[1]), (75, 75))
		self.rect.center = tuple(rect)
		self.image = pygame.image.load('enemyjet.png')
		self.image = pygame.transform.scale(self.image, self.rect.size)
		self.originalImage = self.image
		self.originalRect = self.rect
		self.id = _id

	def move(self, data):
		try:
			pos = data["position"]
			self.rect.centerx = pos[0]
			self.rect.centery = pos[1]
		except KeyError as e:
			pass

	def rotate(self, angle):
		rot_image = pygame.transform.rotate(self.originalImage, angle)
		rot_rect = self.originalRect.copy()
		rot_rect.center = rot_image.get_rect().center
		rot_image = rot_image.subsurface(rot_rect).copy()
		self.image = rot_image

	def tick(self):
		pass

