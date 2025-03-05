from django import forms
from .models import UploadedFile, RAGPool

class UploadFileForm(forms.ModelForm):
    rag_pool = forms.ModelChoiceField(queryset=RAGPool.objects.all(), required=True, label="RAG Pool")

    class Meta:
        model = UploadedFile
        fields = ["rag_pool", "file"]