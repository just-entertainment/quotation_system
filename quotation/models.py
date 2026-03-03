from django.db import models
from django.utils import timezone
import os

class Quotation(models.Model):
    STATUS_CHOICES = (
        ('completed', '完成'),
        ('inquiry', '询单'),
        ('quoted', '报价'),
    )
    
    date = models.DateField(default=timezone.now)
    customer_name = models.CharField(max_length=255)
    project_name = models.CharField(max_length=255, verbose_name='项目名称', default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inquiry')
    folder_path = models.CharField(max_length=500, verbose_name='文件夹路径', default='/quotations')
    
    def __str__(self):
        return f"{self.customer_name} - {self.date} - {self.get_status_display()}"
    
    def get_folder_url(self):
        """获取文件夹的访问路径"""
        return self.folder_path
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 确保folder_path使用正斜杠
        if self.folder_path:
            self.folder_path = self.folder_path.replace('\\', '/')
    
    def save(self, *args, **kwargs):
        """保存时确保文件夹存在"""
        if self.folder_path:
            # 确保路径使用正斜杠
            self.folder_path = self.folder_path.replace('\\', '/')
            if not os.path.exists(self.folder_path):
                os.makedirs(self.folder_path, exist_ok=True)
        super().save(*args, **kwargs)
    
    def get_attachment_counts(self):
        """获取附件类型数量"""
        counts = {'original': 0, 'inquiry': 0, 'quotation': 0}
        if os.path.exists(self.folder_path):
            for sub_folder_name in os.listdir(self.folder_path):
                sub_folder_path = os.path.join(self.folder_path, sub_folder_name).replace('\\', '/')
                if os.path.isdir(sub_folder_path):
                    if sub_folder_name in counts:
                        counts[sub_folder_name] = len(os.listdir(sub_folder_path))
        return counts

class Inquiry(models.Model):
    """询价单模型"""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='inquiries')
    supplier_name = models.CharField(max_length=255, verbose_name='供应商名称')
    contact_info = models.CharField(max_length=255, verbose_name='联系方式')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.supplier_name} - {self.quotation.customer_name}"
    
    def get_folder_path(self):
        """获取询价单文件夹路径"""
        if self.quotation.folder_path:
            inquiry_folder = os.path.join(self.quotation.folder_path, 'inquiry', f"{self.supplier_name}_{self.id}").replace('\\', '/')
            if not os.path.exists(inquiry_folder):
                os.makedirs(inquiry_folder, exist_ok=True)
            return inquiry_folder
        return ''

