from rest_framework import serializers
from .models import CRTSHResult, WebHeaderCheck, WebTechFingerprinting_Results

class CRTSHResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRTSHResult
        fields = '__all__'

class WebHeaderCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebHeaderCheck
        fields = '__all__'

class WebTechFingerprinting_ResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebTechFingerprinting_Results
        fields = '__all__'