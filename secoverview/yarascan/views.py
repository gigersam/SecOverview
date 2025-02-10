import yara
import uuid
import os
from django.shortcuts import render, redirect
from django.http import HttpRequest
from datetime import datetime
from django.contrib.auth.decorators import login_required
from .models import ScanResult
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q

# Define YARA rule (or load from file)
YARA_RULES = """
rule MalwareNamedDocument
{
    meta:
        author = "Your Name"
        description = "Detects document files with 'malware' in the filename"
        date = "2025-02-10"
        reference = "Internal Detection Rule"

    strings:
        $doc_magic = {D0 CF 11 E0 A1 B1 1A E1}  // OLE Compound File (Legacy MS Office)
        $docx_magic = {50 4B 03 04}  // ZIP Header (used in DOCX, XLSX, PPTX)
        $pdf_magic = {25 50 44 46 2D}  // PDF Header

    condition:
        (any of ($doc_magic, $docx_magic, $pdf_magic))
        and
        (filesize < 10MB)  // Optional: Avoid scanning huge files
}
"""

# Compile YARA rule
compiled_rules = yara.compile(source=YARA_RULES)

def scan_file(file_path):
    """Scan a file with YARA and return matched rules."""
    matches = compiled_rules.match(file_path)
    return matches

@login_required
def yara_scan_view(request):
    """Handle file upload, generate a UUID, and scan it with YARA."""
    assert isinstance(request, HttpRequest)
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        file_name = uploaded_file.name

        # Generate a UUID
        scan_uuid = uuid.uuid4()
        folder_path = os.path.join(settings.MEDIA_ROOT, "scans", str(scan_uuid))

        # Create the folder
        os.makedirs(folder_path, exist_ok=True)

        # Save the file inside the UUID-named folder
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Scan the file
        matches = scan_file(file_path)

        # Save results in the database
        result = ScanResult.objects.create(
            uuid=scan_uuid,
            file_name=file_name,
            stored_file_path=file_path,
            matched_rules="\n".join([str(match) for match in matches])
        )

        return render(
            request,
            'yarascan.html',
            {
                'title':'Yara Scan',
                'year':datetime.now().year,
                "result": result, 
                "matches": matches
            }
        )

    return render(
        request,
        'yarascan.html',
        {
            'title':'Yara Scan',
            'year':datetime.now().year,
            "result": "", 
            "matches": ""
        }
    )
    
@login_required
def yara_scan_overview(request):
    assert isinstance(request, HttpRequest)
    query = request.GET.get("search")
    if query == None or query == "":
        scans = ScanResult.objects.order_by('-id')
    else:
        scans = ScanResult.objects.filter(Q(uuid__icontains=query) | Q(file_name__icontains=query) | Q(matched_rules__icontains=query)).order_by('-id')
    paginator = Paginator(scans, 5)
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the appropriate page of blog posts
    return render(
        request,
        'yaraoverview.html',
        {
            'title':'Yara Scan',
            'year':datetime.now().year,
            "results": page_obj, 
        }
    ) 

@login_required
def yarascanreport(request, uuid):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    scans = ScanResult.objects.get(uuid=uuid)
    return render(
        request,
        'yarascanreport.html',
        {
            'title':'Yara Scan Report',
            'year':datetime.now().year,
            'scans':scans,
        }
    )