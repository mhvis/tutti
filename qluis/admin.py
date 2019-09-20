from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import UserAdmin
from django.forms import MultiWidget

from qluis.models import User, Member

admin.site.register(User, UserAdmin)
admin.site.register(Member)