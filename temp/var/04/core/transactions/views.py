from rest_framework import generics
from core.transactions.models import CashAccountTransaction
from core.transactions.serializers import CashAccountTransactionSerializer
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope

class CashAccountTransactionList(generics.ListAPIView):
    serializer_class = CashAccountTransactionSerializer
    permission_classes = [TokenHasReadWriteScope]

    def get_queryset(self):
        iban = self.request.query_params.get('iban', None)
        currency_code = self.request.query_params.get('currencyCode', None)
        booking_date_from = self.request.query_params.get('bookingDateFrom', None)
        booking_date_to = self.request.query_params.get('bookingDateTo', None)
        sort_by = self.request.query_params.get('sortBy', 'bookingDate[ASC]')
        limit = int(self.request.query_params.get('limit', 10))
        offset = int(self.request.query_params.get('offset', 0))

        queryset = CashAccountTransaction.objects.all()

        if iban:
            queryset = queryset.filter(origin_iban=iban)
        if currency_code:
            queryset = queryset.filter(currency_code=currency_code)
        if booking_date_from:
            queryset = queryset.filter(booking_date__gte=booking_date_from)
        if booking_date_to:
            queryset = queryset.filter(booking_date__lte=booking_date_to)

        if sort_by == 'bookingDate[ASC]':
            queryset = queryset.order_by('booking_date')
        elif sort_by == 'bookingDate[DESC]':
            queryset = queryset.order_by('-booking_date')

        return queryset[offset:offset + limit]

class CashAccountTransactionDetail(generics.RetrieveAPIView):
    queryset = CashAccountTransaction.objects.all()
    serializer_class = CashAccountTransactionSerializer
    permission_classes = [TokenHasReadWriteScope]