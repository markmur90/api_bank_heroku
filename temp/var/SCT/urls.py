from django.urls import path
from .views import (
    SepaCreditTransferCreateView,
    SepaCreditTransferDetailsView,
    SepaCreditTransferStatusView,
    SepaCreditTransferCancelView,
    SepaCreditTransferUpdateScaView
)

urlpatterns = [
    path('', SepaCreditTransferCreateView.as_view(), name='create_sepa_credit_transfer'),
    path('<uuid:payment_id>/', SepaCreditTransferDetailsView.as_view(), name='get_sepa_credit_transfer_details'),
    path('<uuid:payment_id>/status/', SepaCreditTransferStatusView.as_view(), name='get_sepa_credit_transfer_status'),
    path('<uuid:payment_id>/cancel/', SepaCreditTransferCancelView.as_view(), name='cancel_sepa_credit_transfer'),
    path('<uuid:payment_id>/update-sca/', SepaCreditTransferUpdateScaView.as_view(), name='update_sca_sepa_credit_transfer'),
]
