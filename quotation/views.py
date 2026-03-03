from django.shortcuts import render, redirect
from django.views import View
from .models import Quotation, Inquiry
from django import forms
from django.urls import reverse
from django.http import JsonResponse
from django.http import HttpResponse
from openpyxl import Workbook
import zipfile
import io
import os

# 工单表单类
class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['customer_name', 'project_name', 'status']
        labels = {
            'customer_name': '客户名称',
            'project_name': '项目名称',
            'status': '状态',
        }

# 询价单表单类
class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ['supplier_name', 'contact_info']
        labels = {
            'supplier_name': '供应商名称',
            'contact_info': '联系方式',
        }

# 工单上传视图
class QuotationUploadView(View):
    # 显示上传表单
    def get(self, request):
        form = QuotationForm()
        return render(request, 'quotation/upload.html', {'form': form})
    
    # 处理上传请求
    def post(self, request):
        customer_name = request.POST.get('customer_name')
        project_name = request.POST.get('project_name')
        status = request.POST.get('status')
        files = request.FILES.getlist('file')
        
        # 允许的文件扩展名
        allowed_extensions = {'.xlsx', '.xls', '.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.txt', '.rtf', '.csv', '.ppt', '.pptx', '.zip', '.rar', '.7z', '.xml', '.json'}
        # 设置Linux的文件夹路径
        base_folder_path = os.path.normpath(r'//DESKTOP-5HEAPOD/quotation')
        
        # 为每个工单创建一个单独的文件夹
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        folder_name = f"{customer_name}_{timestamp}"
        folder_path = os.path.join(base_folder_path, folder_name).replace('\\', '/')
        
        # 确保路径使用正斜杠
        folder_path = folder_path.replace('\\', '/')
        
        # 调试信息
        print(f"base_folder_path: {repr(base_folder_path)}")
        print(f"folder_name: {repr(folder_name)}")
        print(f"folder_path: {repr(folder_path)}")
        
        # 确保工单文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        # 获取附件类型
        attachment_type = request.POST.get('attachment_type', 'original')
        # 根据附件类型创建子文件夹
        sub_folder_path = os.path.join(folder_path, attachment_type).replace('\\', '/')
        # 确保子文件夹存在
        if not os.path.exists(sub_folder_path):
            os.makedirs(sub_folder_path, exist_ok=True)
        
        if files:
            # 验证文件类型
            valid_files = []
            error_message = None
            
            for file in files:
                # 获取文件扩展名
                ext = os.path.splitext(file.name)[1].lower()
                # 检查文件扩展名是否在允许列表中
                if ext not in allowed_extensions:
                        error_message = f"不支持的文件类型: {file.name}。只允许上传xlsx、xls、pdf、jpg、jpeg、png、doc、docx、txt、rtf、csv、ppt、pptx、zip、rar、7z、xml、json文件。"
                        break
                valid_files.append(file)
            
            if error_message:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error_message': error_message}, status=400)
                form = QuotationForm(request.POST)
                return render(request, 'quotation/upload.html', {'form': form, 'error_message': error_message})
            
            # 保存上传的文件到指定子文件夹
            for file in files:
                file_path = os.path.join(sub_folder_path, file.name).replace('\\', '/')
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
        
        # 创建Quotation实例
        quotation = Quotation(
            customer_name=customer_name,
            project_name=project_name,
            status=status,
            folder_path=folder_path
        )
        quotation.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect(reverse('quotation:list'))

# 工单列表视图
class QuotationListView(View):
    def get(self, request):
        quotations = Quotation.objects.all()
        return render(request, 'quotation/list.html', {'quotations': quotations})

# 工单状态更新视图
class QuotationUpdateStatusView(View):
    def post(self, request, pk):
        quotation = Quotation.objects.get(pk=pk)
        quotation.status = request.POST.get('status')
        quotation.save()
        return redirect(reverse('quotation:list'))

# 工单详情视图
class QuotationDetailView(View):
    def get(self, request, pk):
        quotation = Quotation.objects.get(pk=pk)
        # 获取工单的附件列表
        attachments = []
        if os.path.exists(quotation.folder_path):
            # 遍历所有子文件夹
            for sub_folder_name in os.listdir(quotation.folder_path):
                sub_folder_path = os.path.join(quotation.folder_path, sub_folder_name).replace('\\', '/')
                if os.path.isdir(sub_folder_path):
                    for file_name in os.listdir(sub_folder_path):
                        file_path = os.path.join(sub_folder_path, file_name).replace('\\', '/')
                        if os.path.isfile(file_path):
                            attachments.append({
                                'name': file_name,
                                'path': file_path,
                                'folder_path': sub_folder_path,
                                'size': os.path.getsize(file_path),
                                'type': sub_folder_name
                            })
        return render(request, 'quotation/detail.html', {'quotation': quotation, 'attachments': attachments})

# 工单附件管理视图
class QuotationAttachmentsView(View):
    # 显示附件列表
    def get(self, request, pk, attachment_type=None):
        quotation = Quotation.objects.get(pk=pk)
        # 获取工单的附件列表
        attachments = []
        if os.path.exists(quotation.folder_path):
            # 遍历所有子文件夹
            for sub_folder_name in os.listdir(quotation.folder_path):
                sub_folder_path = os.path.join(quotation.folder_path, sub_folder_name).replace('\\', '/')
                if os.path.isdir(sub_folder_path):
                    # 如果指定了附件类型，只返回该类型的附件
                    if attachment_type and sub_folder_name != attachment_type:
                        continue
                    for file_name in os.listdir(sub_folder_path):
                        file_path = os.path.join(sub_folder_path, file_name).replace('\\', '/')
                        if os.path.isfile(file_path):
                            attachments.append({
                                'name': file_name,
                                'path': file_path,
                                'folder_path': sub_folder_path,
                                'size': os.path.getsize(file_path),
                                'type': sub_folder_name
                            })
        # 获取询价单列表
        inquiries = []
        if attachment_type == 'inquiry':
            inquiries = Inquiry.objects.filter(quotation=quotation)
        # 创建询价单表单
        inquiry_form = InquiryForm()
        return render(request, 'quotation/attachments.html', {
            'quotation': quotation, 
            'attachments': attachments, 
            'attachment_type': attachment_type,
            'inquiries': inquiries,
            'inquiry_form': inquiry_form
        })
    
    # 处理附件操作（添加/删除）和新建询价单
    def post(self, request, pk):
        quotation = Quotation.objects.get(pk=pk)
        action = request.POST.get('action')
        # 获取附件类型
        attachment_type = request.POST.get('attachment_type', None)
        
        if action == 'add':
            # 添加新附件
            files = request.FILES.getlist('file')
            allowed_extensions = {'.xlsx', '.xls', '.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.txt', '.rtf', '.csv', '.ppt', '.pptx', '.zip', '.rar', '.7z', '.xml', '.json'}
            
            if files:
                # 验证文件类型
                valid_files = []
                error_message = None
                
                for file in files:
                    # 获取文件扩展名
                    ext = os.path.splitext(file.name)[1].lower()
                    # 检查文件扩展名是否在允许列表中
                    if ext not in allowed_extensions:
                        error_message = f"不支持的文件类型: {file.name}。只允许上传xlsx、xls、pdf、jpg、jpeg、png、doc、docx、txt、rtf、csv、ppt、pptx、zip、rar、7z、xml、json文件。"
                        break
                    valid_files.append(file)
                
                if error_message:
                    # 获取附件列表
                    attachments = []
                    if os.path.exists(quotation.folder_path):
                        # 遍历所有子文件夹
                        for sub_folder_name in os.listdir(quotation.folder_path):
                            sub_folder_path = os.path.join(quotation.folder_path, sub_folder_name).replace('\\', '/')
                            if os.path.isdir(sub_folder_path):
                                for file_name in os.listdir(sub_folder_path):
                                    file_path = os.path.join(sub_folder_path, file_name).replace('\\', '/')
                                    if os.path.isfile(file_path):
                                        attachments.append({
                                            'name': file_name,
                                            'path': file_path,
                                            'size': os.path.getsize(file_path),
                                            'type': sub_folder_name
                                        })
                    # 获取询价单列表
                    inquiries = Inquiry.objects.filter(quotation=quotation)
                    # 创建询价单表单
                    inquiry_form = InquiryForm()
                    return render(request, 'quotation/attachments.html', {
                        'quotation': quotation, 
                        'attachments': attachments, 
                        'attachment_type': attachment_type,
                        'error_message': error_message,
                        'inquiries': inquiries,
                        'inquiry_form': inquiry_form
                    })
                
                # 获取附件类型
                attachment_type = request.POST.get('attachment_type', 'original')
                # 获取询价单ID（如果有）
                inquiry_id = request.POST.get('inquiry_id')
                
                # 确定保存路径
                if inquiry_id and attachment_type == 'inquiry':
                    try:
                        inquiry = Inquiry.objects.get(id=inquiry_id, quotation=quotation)
                        sub_folder_path = inquiry.get_folder_path()
                    except Inquiry.DoesNotExist:
                        sub_folder_path = os.path.join(quotation.folder_path, attachment_type).replace('\\', '/')
                else:
                    sub_folder_path = os.path.join(quotation.folder_path, attachment_type).replace('\\', '/')
                
                # 确保子文件夹存在
                if not os.path.exists(sub_folder_path):
                    os.makedirs(sub_folder_path, exist_ok=True)
                
                # 保存上传的文件到指定子文件夹
                for file in files:
                    file_path = os.path.join(sub_folder_path, file.name).replace('\\', '/')
                    with open(file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
        
        elif action == 'delete':
            # 删除附件
            file_name = request.POST.get('file_name')
            if file_name:
                # 遍历所有子文件夹查找文件
                for sub_folder_name in os.listdir(quotation.folder_path):
                    sub_folder_path = os.path.join(quotation.folder_path, sub_folder_name).replace('\\', '/')
                    if os.path.isdir(sub_folder_path):
                        # 遍历子文件夹内的所有文件和子文件夹
                        for root, dirs, files in os.walk(sub_folder_path):
                            for file in files:
                                if file == file_name:
                                    file_path = os.path.join(root, file).replace('\\', '/')
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                        # 如果子文件夹为空，则删除该子文件夹
                                        if not os.listdir(root):
                                            os.rmdir(root)
                                        # 尝试从文件路径中提取附件类型
                                        if not attachment_type:
                                            # 从文件路径中提取附件类型
                                            path_parts = root.split('/')
                                            if len(path_parts) > 1:
                                                # 查找inquiry、original或quotation在路径中的位置
                                                for part in path_parts:
                                                    if part in ['inquiry', 'original', 'quotation']:
                                                        attachment_type = part
                                                        break
                                        break
        
        elif action == 'add_inquiry':
            # 新建询价单
            form = InquiryForm(request.POST)
            if form.is_valid():
                inquiry = form.save(commit=False)
                inquiry.quotation = quotation
                inquiry.save()
                # 创建询价单文件夹
                inquiry.get_folder_path()
            # 当创建询价单时，确保attachment_type为'inquiry'
            attachment_type = 'inquiry'
        
        elif action == 'delete_inquiry':
            # 删除询价单
            inquiry_id = request.POST.get('inquiry_id')
            if inquiry_id:
                try:
                    inquiry = Inquiry.objects.get(id=inquiry_id, quotation=quotation)
                    # 获取询价单文件夹路径
                    folder_path = inquiry.get_folder_path()
                    # 删除询价单
                    inquiry.delete()
                    # 删除对应的文件夹（如果存在）
                    if folder_path and os.path.exists(folder_path):
                        import shutil
                        shutil.rmtree(folder_path)
                except Inquiry.DoesNotExist:
                    pass
            # 确保attachment_type为'inquiry'
            attachment_type = 'inquiry'
        
        # 获取附件列表
        attachments = []
        if os.path.exists(quotation.folder_path):
            # 遍历所有子文件夹
            for sub_folder_name in os.listdir(quotation.folder_path):
                sub_folder_path = os.path.join(quotation.folder_path, sub_folder_name).replace('\\', '/')
                if os.path.isdir(sub_folder_path):
                    for file_name in os.listdir(sub_folder_path):
                        file_path = os.path.join(sub_folder_path, file_name).replace('\\', '/')
                        if os.path.isfile(file_path):
                            attachments.append({
                                'name': file_name,
                                'path': file_path,
                                'folder_path': sub_folder_path,
                                'size': os.path.getsize(file_path),
                                'type': sub_folder_name
                            })
        
        # 获取询价单列表
        inquiries = Inquiry.objects.filter(quotation=quotation)
        # 创建询价单表单
        inquiry_form = InquiryForm()
        
        # 返回渲染后的模板
        return render(request, 'quotation/attachments.html', {
            'quotation': quotation, 
            'attachments': attachments, 
            'attachment_type': attachment_type,
            'inquiries': inquiries,
            'inquiry_form': inquiry_form
        })

# 工单搜索视图
class QuotationSearchView(View):
    def get(self, request):
        customer_name = request.GET.get('customer_name')
        project_name = request.GET.get('project_name')
        date = request.GET.get('date')
        status = request.GET.get('status')
        
        quotations = Quotation.objects.all()
        
        if customer_name:
            quotations = quotations.filter(customer_name__icontains=customer_name)
        if project_name:
            quotations = quotations.filter(project_name__icontains=project_name)
        if date:
            quotations = quotations.filter(date=date)
        if status:
            quotations = quotations.filter(status=status)
        
        return render(request, 'quotation/list.html', {'quotations': quotations})

# 工单导出视图
class QuotationExportView(View):
    def get(self, request):
        customer_name = request.GET.get('customer_name')
        project_name = request.GET.get('project_name')
        date = request.GET.get('date')
        status = request.GET.get('status')
        
        quotations = Quotation.objects.all()
        
        if customer_name:
            quotations = quotations.filter(customer_name__icontains=customer_name)
        if project_name:
            quotations = quotations.filter(project_name__icontains=project_name)
        if date:
            quotations = quotations.filter(date=date)
        if status:
            quotations = quotations.filter(status=status)
        
        # 创建Excel工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = '工单列表'
        
        # 添加表头
        headers = ['日期', '客户名称', '项目名称', '状态', '原单数量', '询价单数量', '报价单数量']
        ws.append(headers)
        
        # 添加数据
        for quotation in quotations:
            counts = quotation.get_attachment_counts()
            ws.append([
                quotation.date.strftime('%Y-%m-%d') if quotation.date else '',
                quotation.customer_name,
                quotation.project_name,
                quotation.get_status_display(),
                counts['original'],
                counts['inquiry'],
                counts['quotation']
            ])
        
        # 设置响应
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="工单列表.xlsx"'
        
        # 保存工作簿到响应
        wb.save(response)
        
        return response

# 工单下载视图
class QuotationDownloadView(View):
    def get(self, request, pk):
        from django.http import FileResponse
        import os
        
        quotation = Quotation.objects.get(pk=pk)
        file_name = request.GET.get('file')
        
        if file_name:
            # 遍历所有子文件夹查找文件
            for sub_folder_name in os.listdir(quotation.folder_path):
                sub_folder_path = os.path.join(quotation.folder_path, sub_folder_name).replace('\\', '/')
                if os.path.isdir(sub_folder_path):
                    file_path = os.path.join(sub_folder_path, file_name).replace('\\', '/')
                    if os.path.exists(file_path):
                        response = FileResponse(open(file_path, 'rb'))
                        response['Content-Disposition'] = f'attachment; filename={file_name}'
                        return response
        
        return redirect(reverse('quotation:attachments', args=[pk]))

# 工单全部附件下载视图
class QuotationDownloadAllView(View):
    def get(self, request, pk):
        from django.http import FileResponse
        import os
        import zipfile
        import tempfile
        
        quotation = Quotation.objects.get(pk=pk)
        folder_path = quotation.folder_path
        
        if os.path.exists(folder_path):
            # 创建临时文件夹
            temp_dir = tempfile.mkdtemp()
            
            # 创建zip文件
            zip_name = f"{quotation.customer_name}_{quotation.project_name}_附件.zip"
            zip_path = os.path.join(temp_dir, zip_name).replace('\\', '/')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历所有子文件夹中的文件
                for sub_folder_name in os.listdir(folder_path):
                    sub_folder_path = os.path.join(folder_path, sub_folder_name).replace('\\', '/')
                    if os.path.isdir(sub_folder_path):
                        for file_name in os.listdir(sub_folder_path):
                            file_path = os.path.join(sub_folder_path, file_name).replace('\\', '/')
                            if os.path.isfile(file_path):
                                # 将文件添加到zip文件中，保留子文件夹结构
                                arcname = os.path.join(sub_folder_name, file_name).replace('\\', '/')
                                zipf.write(file_path, arcname=arcname)
            
            # 返回zip文件
            response = FileResponse(open(zip_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename={zip_name}'
            
            # 清理临时文件
            def cleanup():
                import shutil
                shutil.rmtree(temp_dir)
            
            # 注册清理函数
            import atexit
            atexit.register(cleanup)
            
            return response
        
        return redirect(reverse('quotation:attachments', args=[pk]))



