from rest_framework import serializers
#from accounts.models import CustomUser
from mlnids.models import NetworkFlow
from webops.models import CRTSHResult, WebHeaderCheck, WebTechFingerprinting_Results

#class UserSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = CustomUser
#        fields = ['id', 'username', 'email', 'phone_number']

class NetworkFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkFlow
        fields = '__all__'

class CRTSHResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRTSHResult
        fields = ['result']

class WebHeaderCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebHeaderCheck
        exclude = ['id']

class WebTechFingerprinting_ResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebTechFingerprinting_Results
        exclude = ['id','domain']
