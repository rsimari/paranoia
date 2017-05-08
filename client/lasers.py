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

# laser objects that get shot player
class Laser(pygame.sprite.Sprite):
	def __init__(self, x, y, dx, dy, rot, gs):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load('laser.png')
		self.rect = pygame.Rect((x, y), (15, 5))

		self.image = pygame.transform.scale(self.image, self.rect.size)

		# rotate image
		self.angle = -math.degrees(rot)
		rot_image = pygame.transform.rotate(self.image, self.angle)
		#rot_rect = self.rect.copy()
		#rot_rect.center = rot_image.get_rect().center
		#rot_image = rot_image.subsurface(rot_rect).copy()
		self.image = rot_image
		self.rect = self.image.get_rect()
		self.rect.centerx = x
		self.rect.centery = y

		self.speed = 20
		self.gs = gs
		self.dx = dx
		self.dy = dy

	def tick(self):
		#ngl = math.radians(self.angle + 90)
		#self.rect.centerx += (self.speed * math.sin(ngl))
		#self.rect.centery += (self.speed * math.cos(ngl))
		
		# no longer need to pass dx dy
		self.rect.centerx += (self.speed * self.dx)
		self.rect.centery += (self.speed * self.dy)
		# detect collision
		for _id, e in self.gs.enemies.iteritems():
			if self.rect.colliderect(e.rect):
				self.gs.game_objects.remove(self)

class EnemyLaser(pygame.sprite.Sprite):
	def __init__(self, x, y, dx, dy, player, gs):
		pygame.sprite.Sprite.__init__(self)

		self.rect = pygame.Rect((x, y), (15, 5))
		self.image = pygame.image.load('enemylaser.png')
		self.image = pygame.transform.scale(self.image, self.rect.size)

		# rotate image
		# pass rot in and try this !!!!!
		rot = math.tan(dy/dx)
		self.angle = math.degrees(rot)
		rot_image = pygame.transform.rotate(self.image, self.angle)
		#rot_rect = self.rect.copy()
		#rot_rect.center = rot_image.get_rect().center
		#rot_image = rot_image.subsurface(rot_rect).copy()
		self.image = rot_image
		self.rect = self.image.get_rect()
		self.rect.centerx = x
		self.rect.centery = y


		self.target = player
		self.gs = gs
		self.speed = 20
		self.dx = dx
		self.dy = dy

	def tick(self):
		#ngl = math.radians(self.angle + 90)
		#self.rect.centerx += (self.speed * math.sin(ngl))
		#self.rect.centery += (self.speed * math.cos(ngl))

		# no longer need to pass dx dy
		self.rect.centerx += (self.speed * self.dx)
		self.rect.centery += (self.speed * self.dy)

		# detect collision
		if self.rect.colliderect(self.target.rect):
			if self.target.health > 0:
				self.target.health -= 10
				# remove laser from game
				self.gs.game_objects.remove(self)
