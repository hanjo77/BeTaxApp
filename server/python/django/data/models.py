from django.db import models
from django.utils import timezone

class Driver(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    token = models.CharField(max_length=255)
    last_login = models.DateTimeField(auto_now=True)

class Taxi(models.Model):
    name = models.CharField(max_length=255)

class Position(models.Model):
    driver = models.ForeignKey(Driver)
    taxi = models.ForeignKey(Taxi)
    latitude = models.FloatField()
    longitude = models.FloatField()
    time = models.DateTimeField(auto_now_add=True)
