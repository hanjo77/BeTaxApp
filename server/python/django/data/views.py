from django.shortcuts import render
from django.views import generic
from data.models import Taxi

class MenuView(generic.list.ListView):
    model = Taxi
