from django.db import models
from django.utils import timezone

class Quotation(models.Model):
    STATUS_CHOICES = (
        ('completed', '完成'),
        ('inquiry', '询单'),
        ('quoted', '报价'),
    )
    
    date = models.DateField(default=timezone.now)
    customer_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inquiry')
    file = models.FileField(upload_to='quotations/')
    
    def __str__(self):
        return f"{self.customer_name} - {self.date} - {self.get_status_display()}"

