from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.core.paginator import Paginator
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .livingoffland_ops import INVOKEARGFUSCATOR, get_lolbas_data, get_gtfobins_data, obfuscate_command_invokeargfusctor, obfuscate_command_base64
from .models import LOLBASBinary, GTFObinsBinary, GTFObinsFunction

@login_required
def livingoffland(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        domain = request.POST.get('domain')
        livingofflanddata = LOLBASBinary.objects.with_all_related().get(pk=domain)
        return render(
            request,
            'livingoffland.html',
            {
                'title':'Living of the Land',
                'year':datetime.now().year,
                'livingoflanddata':livingofflanddata,
                'chatcontext':"" 
            }
        )

    else:
        livingofflanddata = LOLBASBinary.objects.with_all_related().all()
        return render(
            request,
            'livingoffland.html',
            {
                'title':'Living of the Land',
                'year':datetime.now().year,
                'livingoflanddata':livingofflanddata,
                'chatcontext':""
            }
        )

def livingofflandupdate(request):
    #get_lolbas_data()
    get_gtfobins_data()
    return redirect('livingoffland')

def livingofflandcommandsearch(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    categories = (
        LOLBASBinary.objects.with_all_related()
        .values_list('commands__category', flat=True)
        .exclude(commands__category__isnull=True)
        .exclude(commands__category__iexact='')
        .distinct()
        .order_by('commands__category')
    )

    linuxcategories = GTFObinsFunction.objects.all()

    mitre_ids = (
        LOLBASBinary.objects.with_all_related()
        .values_list('commands__mitre_id', flat=True)
        .exclude(commands__mitre_id__isnull=True)
        .exclude(commands__mitre_id__iexact='')
        .distinct()
        .order_by('commands__mitre_id')
    )

    if request.method == 'POST':
        category = request.POST.get('category')
        mitre_id = request.POST.get('mitre_id')
        windows = bool(request.POST.get("windows"))
        linux = bool(request.POST.get("linux"))
        #os = request.POST.get('os')
        

        if windows:
            qs = LOLBASBinary.objects.with_all_related()
            q = Q()
            if category and category.strip().lower() != "none":
                q &= Q(commands__category=category.strip())
            if mitre_id and mitre_id.strip().lower() != "none":
                q &= Q(commands__mitre_id=mitre_id.strip())

            livingofflanddata = qs.filter(q).distinct()        #livingofflanddata = LOLBASBinary.objects.with_all_related().get(pk=domain)
        else:
            livingofflanddata = None
        if linux:
            qs = GTFObinsBinary.objects.with_all_related()
            q = Q()
            if category and category.strip().lower() != "none":
                q &= Q(function_examples__function__name=category.strip())
            if mitre_id and mitre_id.strip().lower() != "none":
                q &= Q(function_examples__function__description="Empty")
            gtfobinsdata = qs.filter(q).distinct()
        else:
            gtfobinsdata = None
        
        if not windows and not linux:
            gtfobinsdata = None
            livingofflanddata = None

        return render(
            request,
            'livingofflandcommandsearch.html',
            {
                'title':'Living of the Land Command Creator',
                'year':datetime.now().year,
                'livingoflanddata':livingofflanddata,
                'gtfobinsdata':gtfobinsdata,
                'categories':categories,
                'linuxcategories':linuxcategories,
                'selected_category':category,
                'mitre_ids':mitre_ids,
                'selected_mitre_id':mitre_id,
                'chatcontext':"" 
            }
        )

    else:
        return render(
            request,
            'livingofflandcommandsearch.html',
            {
                'title':'Living of the Land Command Creator',
                'year':datetime.now().year,
                'livingoflanddata':"",
                'gtfobinsdata':"",
                'categories':categories,
                'linuxcategories':linuxcategories,
                'mitre_ids':mitre_ids,
                'chatcontext':""
            }
        )
    
def livingofflandbinary(request, binary):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    livingoflanddata = LOLBASBinary.objects.with_all_related().filter(id=binary)
    return render(
            request,
            'livingofflandbinary.html',
            {
                'title':'Living of the Land Command Searcher',
                'year':datetime.now().year,
                'livingoflanddata':livingoflanddata[0],
                'chatcontext':""
            }
        )

def gtfobinsbinary(request, binary):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    gtfobinsdata = GTFObinsBinary.objects.with_all_related().filter(id=binary)
    return render(
            request,
            'gtfobinsbinary.html',
            {
                'title':'Living of the Land Command Searcher',
                'year':datetime.now().year,
                'gtfobinsdata':gtfobinsdata[0],
                'chatcontext':""
            }
        )

def commandcreatorwindows(request, binary):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    binary = LOLBASBinary.objects.with_all_related().filter(id=binary)
    if request.method == 'POST':
        category = request.POST.get("category")
        command = request.POST.get("command")
        print((binary[0].name).replace(".exe", ""))
        #binary = LOLBASBinary.objects.with_all_related().filter(id=binary)
        if (binary[0].name).replace(".exe", "").lower() in INVOKEARGFUSCATOR:
            obfuscated = obfuscate_command_invokeargfusctor(command)
            obfuscationmethod = "Invoke-ArgFuscator by wietze"
        else:
            obfuscated = obfuscate_command_base64(command, 'windows')
            obfuscationmethod = "Base64"
        return render(
                request,
                'commandcreatorwindows.html',
                {
                    'title':'Living of the Land Command Creator',
                    'year':datetime.now().year,
                    'binary':binary[0],
                    'category':category,
                    'command':command,
                    'obfuscated':obfuscated,
                    'obfuscationmethod':obfuscationmethod,
                    'chatcontext':""
                }
            )
    else:
        category = request.GET.get("category")
        #binary = LOLBASBinary.objects.with_all_related().filter(id=binary)

        return render(
                request,
                'commandcreatorwindows.html',
                {
                    'title':'Living of the Land Command Creator',
                    'year':datetime.now().year,
                    'binary':binary[0],
                    'category':category,
                    'command':"",
                    'obfuscated':"",
                    'chatcontext':""
                }
            )

def commandcreatorlinux(request, binary):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    category = request.GET.get("category")
    if category == "None":
        binary = GTFObinsBinary.objects.with_all_related().filter(id=binary)
    else:
        binary = GTFObinsBinary.objects.with_all_related().filter(Q(id=binary) & Q(function_examples__function__name=category.strip()))

    return render(
            request,
            'commandcreatorlinux.html',
            {
                'title':'Living of the Land Command Creator',
                'year':datetime.now().year,
                'binary':binary[0],
                'chatcontext':""
            }
        )