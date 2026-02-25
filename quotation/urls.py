from django.urls import path
from .views import QuotationUploadView, QuotationListView, QuotationUpdateStatusView, QuotationSearchView

app_name = 'quotation'

urlpatterns = [
    path('upload/', QuotationUploadView.as_view(), name='upload'),
    path('list/', QuotationListView.as_view(), name='list'),
    path('update-status/<int:pk>/', QuotationUpdateStatusView.as_view(), name='update_status'),
    path('search/', QuotationSearchView.as_view(), name='search'),
]