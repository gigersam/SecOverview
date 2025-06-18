from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.conf import settings
from datetime import datetime
from django.contrib.auth.decorators import login_required
from .models import RansomwareliveGroupsGroup, RansomwareliveVictim
from .ransomwareliveops import fetch_ransomwarelive_groups, fetch_ransomwarelive_victims
from django.db.models import Q

@login_required
def ransomwarelive(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    victims = RansomwareliveVictim.objects.order_by('-id')[:5]
    groups = RansomwareliveGroupsGroup.objects.order_by('-id')[:5]
    return render(
        request,
        'ransomwarelive.html',
        {
            'title':'Ransomwarelive Overview',
            'year':datetime.now().year,
            'victims':victims,
            'groups':groups,
            'chatcontext':f"Shows the latest ransomware live updates. Groups: {groups}, victims: {victims}" 
        }
    )

@login_required
def ransomwareliveupdate(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    fetch_ransomwarelive_groups()
    fetch_ransomwarelive_victims()
    return redirect(ransomwarelive)

@login_required
def victimsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    if query == None or query == "":
        victims = RansomwareliveVictim.objects.order_by('-id')
    else:
        victims = RansomwareliveVictim.objects.filter(Q(post_title__icontains=query) | Q(country__icontains=query) | Q(description__icontains=query) | Q(activity__icontains=query)).order_by('-id')
    paginator = Paginator(victims, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'victimsoverview.html',
        {
            'title':'Ransomwarelive Victims Overview',
            'year':datetime.now().year,
            'victims':page_obj,
            'chatcontext':f"Shows Ransomwarelive Victims. Victims: {page_obj}" 
        }
    )

@login_required
def victimview(request, id):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    victims = RansomwareliveVictim.objects.get(id=id)
    return render(
        request,
        'victimview.html',
        {
            'title':'Ransomwarelive Victim',
            'year':datetime.now().year,
            'victims':victims,
            'chatcontext':f"Shows Ransomwarelive Victim {victims}" 
        }
    )

@login_required
def groupsoverview(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    if query == None or query == "":
        groups = RansomwareliveGroupsGroup.objects.order_by('-id')
    else:
        groups = RansomwareliveGroupsGroup.objects.filter(Q(name__icontains=query)).order_by('-id')
    paginator = Paginator(groups, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'groupsoverview.html',
        {
            'title':'Ransomwarelive Groups Overview',
            'year':datetime.now().year,
            'groups':page_obj,
            'chatcontext':f"Shows Ransomwarelive Groups. Groups: {page_obj}" 
        }
    )
@login_required
def groupview(request, id):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    groups = RansomwareliveGroupsGroup.objects.get(id=id)
    return render(
        request,
        'groupview.html',
        {
            'title':'Ransomwarelive Group',
            'year':datetime.now().year,
            'groups':groups,
            'chatcontext':f"Shows Ransomwarelive Group: {groups}" 
        }
    )

