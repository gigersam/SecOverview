from rest_framework import serializers
from accounts.models import CustomUser
from mlnids.models import NetworkFlow

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number']

class NetworkFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkFlow
        fields = '__all__'