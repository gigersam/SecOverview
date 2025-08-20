from rest_framework import serializers
from .models import Bot, Task

class BotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bot
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'