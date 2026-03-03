from django.urls import path
from .views import QuotationUploadView, QuotationListView, QuotationUpdateStatusView, QuotationSearchView, QuotationDetailView, QuotationAttachmentsView, QuotationDownloadView, QuotationDownloadAllView, QuotationExportView

app_name = 'quotation'

urlpatterns = [
    path('upload/', QuotationUploadView.as_view(), name='upload'),
    path('list/', QuotationListView.as_view(), name='list'),
    path('detail/<int:pk>/', QuotationDetailView.as_view(), name='detail'),
    path('attachments/<int:pk>/<str:attachment_type>/', QuotationAttachmentsView.as_view(), name='attachments'),
    path('attachments/<int:pk>/', QuotationAttachmentsView.as_view(), name='attachments'),
    path('download/<int:pk>/', QuotationDownloadView.as_view(), name='download'),
    path('download-all/<int:pk>/', QuotationDownloadAllView.as_view(), name='download_all'),
    path('export/', QuotationExportView.as_view(), name='export'),
    path('update-status/<int:pk>/', QuotationUpdateStatusView.as_view(), name='update_status'),
    path('search/', QuotationSearchView.as_view(), name='search'),
]