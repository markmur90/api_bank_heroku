@require_http_methods(["POST"])
def retry_sepa_transfer_auth(request, payment_id):
    """Reintenta autenticación para segundo factor (tan retry)"""
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'otp': request.POST.get('otp', 'PUSHTAN'),
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': settings.ORIGIN,
        }

        payload = {
            "requestType": "SEPA_TRANSFER_GRANT"
        }

        response = oauth.patch(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer/{payment_id}',
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            logger.info(f"Reintento de autenticación exitoso para: {payment_id}")
            return render(request, 'api/SCT/retry_success.html', {
                'transfer': transfer
            })
        else:
            ErrorResponse.objects.create(
                code=response.status_code,
                message=response.text,
                message_id=headers['idempotency-id']
            )
            logger.warning(f"Fallo al reintentar autenticación: {response.text}")
            return HttpResponseBadRequest("Error al reintentar la autenticación")

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error en retry auth: {str(e)}"
        )
        logger.exception("Error en retry autenticación")
        return HttpResponseServerError("Error en retry autenticación")

