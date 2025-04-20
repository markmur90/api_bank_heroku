@require_http_methods(["POST"])
def cancel_sepa_transfer(request, payment_id):
    """Cancela una transferencia SEPA ya iniciada"""
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'otp': request.POST.get('otp', 'PUSHTAN'),
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': settings.ORIGIN,
        }

        response = oauth.delete(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer/{payment_id}',
            headers=headers
        )

        if response.status_code == 200:
            transfer.transaction_status = 'CANC'
            transfer.save()
            logger.info(f"Transferencia cancelada: {payment_id}")
            return render(request, 'api/SCT/cancel_success.html', {
                'transfer': transfer
            })
        else:
            ErrorResponse.objects.create(
                code=response.status_code,
                message=response.text,
                message_id=headers['idempotency-id']
            )
            logger.error(f"Cancelación fallida: {response.text}")
            return HttpResponseBadRequest("No se pudo cancelar la transferencia.")

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error en cancelación: {str(e)}"
        )
        logger.exception("Error cancelando transferencia")
        return HttpResponseServerError("Error cancelando la transferencia")

