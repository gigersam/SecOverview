from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import ChatMessage
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"  # Adjust if needed
OLLAMA_MODEL = "deepseek-r1:8b"  # Change to your model name

@login_required
def chatpage(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == "POST":
        user_input = request.POST.get("user_input")
        print(user_input)
        
        # Send request to Ollama
        payload = {"model": OLLAMA_MODEL, "prompt": user_input}
        response = requests.post(OLLAMA_URL, json=payload)
        
        print(response.content)

        if response.status_code == 200:
            model_response = response.json().get("response", "Error: No response from model")
            
            # Save to database
            chat = ChatMessage.objects.create(user_input=user_input, model_response=model_response)

            return JsonResponse({"response": model_response})
        else:
            return JsonResponse({"response": "Error communicating with model"}, status=500)
    
    messages = ChatMessage.objects.all().order_by("-timestamp")[:10]
    return render(
        request,
        'chatpage.html',
        {
            'title':'Chat',
            'year':datetime.now().year,
            'messages':messages
        }
    )
