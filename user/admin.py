from django.contrib import admin
from .models import User, Staff, Section, Position, Role, Performance, Vacation, Notice, Out, Leave, Punch, Message

# Register your models here.
admin.site.register(User)
admin.site.register(Staff)
admin.site.register(Section)
admin.site.register(Position)
admin.site.register(Role)
admin.site.register(Performance)
admin.site.register(Vacation)
admin.site.register(Notice)
admin.site.register(Out)
admin.site.register(Leave)
admin.site.register(Punch)
admin.site.register(Message)
