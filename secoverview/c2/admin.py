from django.contrib import admin
from .models import Bot, Task, TaskCommands, Campain, CampainTemplates

admin.site.register(Bot)
admin.site.register(Task)
admin.site.register(TaskCommands)
admin.site.register(Campain)
admin.site.register(CampainTemplates)