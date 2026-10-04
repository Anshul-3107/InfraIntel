from django.contrib import admin

from .models import Infrastructure, Inspection

admin.site.register(Infrastructure)
admin.site.register(Inspection)