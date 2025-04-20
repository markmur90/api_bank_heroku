def check_transfer_status(request, payment_id):
    """Consulta el estado de una transferencia SEPA en formato JSON"""
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json',
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {access_token}",
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': settings.ORIGIN,
        }

        response = oauth.get(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer/{payment_id}/status',
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            new_status = data.get('transactionStatus')
            if new_status:
                transfer.transaction_status = new_status
                transfer.save()
        else:
            logger.warning(f"Respuesta no exitosa del banco: {response.status_code} - {response.text}")

        return render(request, 'api/SCT/transfer_status.html', {
            'transfer': transfer,
            'bank_response': response.json() if response.ok else None
        })

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error consultando estado: {str(e)}"
        )
        logger.exception("Error consultando estado de transferencia")
        return render(request, 'api/SCT/transfer_status.html', {
            'transfer': transfer,
            'error': str(e)
        })

