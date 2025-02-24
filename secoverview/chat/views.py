from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import ChatMessage
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"  # Adjust if needed
OLLAMA_MODEL = "deepseek-r1:8b"  # Change to your model name

@login_required
def chatpage(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == "POST":
        user_input = request.POST.get("user_input")
        print(user_input)
        
        # Send request to Ollama
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": user_input}]
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(OLLAMA_URL, data=json.dumps(payload), headers=headers)
        
        print(response.content)

        if response.status_code == 200:
            #response_content = json.loads(response.content.decode("utf-8"))
            model_response = response.content.decode("utf-8")
            model_response_fomated = model_response.replace("\n", ",\n")
            json_format = ("[" + model_response_fomated + "]").replace(",\n]", "]")
            print(json_format)
            response_content = json.loads(json_format)
            #print(model_response)
            #model_response_fomated = model_response.replace("\n", ",\n")
            #json_model_response = []
            #for input in model_response:
            #    json_model_response += input
            #
            #json_model_response = json_model_response.json()
            #print(json_model_response)
            print(response_content)
            response_string = ""
            for item in response_content:
                response_string += str(item.get("message", {}).get("content", ""))
            json_response = {
                "model": response_content[0].get("model", ""),
                "message": response_string,
                "tokens_used": response_content[-1].get("eval_tokens", 0)
            }

            # Save to database
            chat = ChatMessage.objects.create(user_input=user_input, model_response=json_response)

            return JsonResponse({"response": json_response})
        else:
            return JsonResponse({"response": "Error communicating with model"}, status=500)
    
    messages = ChatMessage.objects.all().order_by("-timestamp")[:10]
    return render(
        request,
        'chatpage.html',
        {
            'title':'Chat',
            'year':datetime.now().year,
            'messages':messages,
            'chatnotavailable':True
        }
    )
