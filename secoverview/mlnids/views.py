from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import NetworkFlow

@login_required
def mlnidsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    flowdata = NetworkFlow.objects.filter(false_positiv=False).order_by('id')
    paginator = Paginator(flowdata, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'mlnidsoverview.html',
        {
            'title':'ML NIDS',
            'year':datetime.now().year,
            'flows':page_obj,
            'chatcontext':"Shows ML analysed detections on the network." 
        }
    )

@login_required
def mlnidsdetection(request, pk):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    if request.method == 'POST':
        falsepositiv = request.POST.get('falsepositiv')
        id = request.POST.get('id')
        NetworkFlow.objects.filter(pk=id).update(false_positiv=falsepositiv)
        return redirect('mlnidsoverview')
    flowdata = NetworkFlow.objects.get(pk=pk)
    return render(
        request,
        'mlnidsdetection.html',
        {
            'title':'ML NIDS',
            'year':datetime.now().year,
            'flow':flowdata,
            'chatcontext':f"Shows ML analysed detections. IF = Isolated Forest, RF = Random Forest. Value: {flowdata}" 
        }
    )
