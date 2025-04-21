from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import SepaCreditTransfer
from .serializers import SepaCreditTransferSerializer

class SepaCreditTransferViewSet(viewsets.ViewSet):
    def create(self, request):
        serializer = SepaCreditTransferSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            transfer = SepaCreditTransfer.objects.get(payment_id=pk)
            serializer = SepaCreditTransferSerializer(transfer)
            return Response(serializer.data)
        except SepaCreditTransfer.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request):
        transfers = SepaCreditTransfer.objects.all()
        serializer = SepaCreditTransferSerializer(transfers, many=True)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        try:
            transfer = SepaCreditTransfer.objects.get(payment_id=pk)
            transfer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SepaCreditTransfer.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
