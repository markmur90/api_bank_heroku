from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    SepaCreditTransferRequest, SepaCreditTransferResponse, 
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest
)
from .serializers import (
    SepaCreditTransferRequestSerializer, SepaCreditTransferResponseSerializer, 
    SepaCreditTransferDetailsResponseSerializer, SepaCreditTransferUpdateScaRequestSerializer
)

class SepaCreditTransferCreateView(APIView):
    """
    View para crear una transferencia SEPA.
    """
    def post(self, request):
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {
                "transaction_status": "PDNG",
                "payment_id": "generated-payment-id",
                "auth_id": "generated-auth-id"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SepaCreditTransferDetailsView(APIView):
    """
    View para obtener los detalles de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferDetailsResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferDetailsResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferDetailsResponse.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)

class SepaCreditTransferStatusView(APIView):
    """
    View para obtener el estado de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferResponse.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)

class SepaCreditTransferCancelView(APIView):
    """
    View para cancelar una transferencia SEPA.
    """
    def delete(self, request, payment_id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=payment_id)
            transfer.delete()
            return Response({"message": "Transfer cancelled successfully"}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)

class SepaCreditTransferUpdateScaView(APIView):
    """
    View para actualizar el segundo factor de autenticación (SCA) de una transferencia SEPA.
    """
    def patch(self, request, payment_id):
        try:
            transfer = SepaCreditTransferUpdateScaRequest.objects.get(id=payment_id)
            serializer = SepaCreditTransferUpdateScaRequestSerializer(transfer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "SCA updated successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SepaCreditTransferUpdateScaRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)
