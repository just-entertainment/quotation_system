from django.shortcuts import render, redirect
from django.views import View
from .models import Quotation
from django import forms
from django.urls import reverse
import zipfile
import io
import os

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['customer_name', 'status', 'file']
        labels = {
            'customer_name': '客户名称',
            'status': '状态',
            'file': '文件',
        }

class QuotationUploadView(View):
    def get(self, request):
        form = QuotationForm()
        return render(request, 'quotation/upload.html', {'form': form})
    
    def post(self, request):
        customer_name = request.POST.get('customer_name')
        status = request.POST.get('status')
        files = request.FILES.getlist('file')
        
        # 允许的文件扩展名
        allowed_extensions = {'.xlsx', '.pdf', '.jpg', '.jpeg', '.png'}
        
        if files:
            # 验证文件类型
            valid_files = []
            error_message = None
            
            for file in files:
                # 获取文件扩展名
                ext = os.path.splitext(file.name)[1].lower()
                # 检查文件扩展名是否在允许列表中
                if ext not in allowed_extensions:
                    error_message = f"不支持的文件类型: {file.name}。只允许上传xlsx、pdf、jpg、png文件。"
                    break
                valid_files.append(file)
            
            if error_message:
                form = QuotationForm(request.POST)
                return render(request, 'quotation/upload.html', {'form': form, 'error_message': error_message})
            
            # 如果上传的是多个文件（文件夹），压缩成zip文件
            if len(files) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file in files:
                        # 保留完整的文件路径结构，确保解压后能恢复原始文件夹结构
                        # Django会将文件夹路径作为文件名的一部分，格式为：文件夹名/子文件夹名/文件名
                        file_path = file.name
                        # 写入文件时保留完整路径，这样解压后会自动创建文件夹结构
                        zip_file.writestr(file_path, file.read())
                
                # 创建一个InMemoryUploadedFile对象
                from django.core.files.uploadedfile import InMemoryUploadedFile
                # 尝试从第一个文件路径中提取文件夹名
                first_file_path = files[0].name
                folder_name = first_file_path.split('/')[0] if '/' in first_file_path else 'quotation'
                zip_file_name = f"{customer_name}_{folder_name}.zip"
                zip_file = InMemoryUploadedFile(
                    zip_buffer,
                    'file',
                    zip_file_name,
                    'application/zip',
                    zip_buffer.tell(),
                    None
                )
                
                # 创建Quotation实例
                quotation = Quotation(
                    customer_name=customer_name,
                    status=status,
                    file=zip_file
                )
                quotation.save()
            else:
                # 如果只上传了一个文件，直接保存
                form = QuotationForm(request.POST, request.FILES)
                if form.is_valid():
                    form.save()
            
            return redirect(reverse('quotation:list'))
        
        # 如果没有文件，返回错误
        form = QuotationForm(request.POST)
        return render(request, 'quotation/upload.html', {'form': form})

class QuotationListView(View):
    def get(self, request):
        quotations = Quotation.objects.all()
        return render(request, 'quotation/list.html', {'quotations': quotations})

class QuotationUpdateStatusView(View):
    def post(self, request, pk):
        quotation = Quotation.objects.get(pk=pk)
        quotation.status = request.POST.get('status')
        quotation.save()
        return redirect(reverse('quotation:list'))

class QuotationSearchView(View):
    def get(self, request):
        customer_name = request.GET.get('customer_name')
        date = request.GET.get('date')
        status = request.GET.get('status')
        
        quotations = Quotation.objects.all()
        
        if customer_name:
            quotations = quotations.filter(customer_name__icontains=customer_name)
        if date:
            quotations = quotations.filter(date=date)
        if status:
            quotations = quotations.filter(status=status)
        
        return render(request, 'quotation/list.html', {'quotations': quotations})

