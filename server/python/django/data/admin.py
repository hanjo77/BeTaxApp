from django.contrib import admin

from .models import Driver
from .models import Taxi

admin.site.register(Driver)
admin.site.register(Taxi)