@require_http_methods(["GET", "POST"])
def initiate_sepa_transfer(request):
    """Vista para iniciar transferencia SEPA (envía JSON a la API del banco)"""
    if request.method == 'POST':
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json'
        }
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            try:
                transfer = form.save(commit=False)
                transfer.payment_id = uuid.uuid4()
                transfer.auth_id = uuid.uuid4()
                transfer.transaction_status = 'PDNG'
                transfer.payment_identification.end_to_end_id = uuid.uuid4().hex[:36]
                transfer.payment_identification.instruction_id = uuid.uuid4().hex[:36]
                transfer.payment_identification.save()
                transfer.save()

                # Preparar JSON payload según especificación del banco
                payload = generate_sepa_json_payload(transfer)

                # Actualizar headers para JSON
                headers.update({
                    'Content-Type': 'application/json',
                    'otp': request.POST.get('otp', 'PUSHTAN'),
                    'Correlation-ID': str(uuid.uuid4()),
                    'Authorization': f"Bearer {access_token}",
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': settings.ORIGIN,
                })

                oauth = get_oauth_session(request)
                response = oauth.post(
                    'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer',
                    json=payload,
                    headers=headers
                )

                if response.status_code == 201:
                    logger.info(f"Transferencia {transfer.payment_id} enviada exitosamente")
                    return render(request, 'api/SCT/transfer_success.html', {
                        'payment_id': transfer.payment_id
                    })
                else:
                    ErrorResponse.objects.create(
                        code=response.status_code,
                        message=response.text,
                        message_id=headers['idempotency-id']
                    )
                    logger.error(f"Error del banco: {response.text}")
                    return HttpResponseBadRequest("Error en la operación bancaria")

            except Exception as e:
                ErrorResponse.objects.create(
                    code=500,
                    message=str(e),
                    message_id=headers.get('idempotency-id', '')
                )
                logger.exception("Error interno procesando transferencia")
                return HttpResponseServerError("Error interno del servidor")
    else:
        form = SepaCreditTransferForm()

    return render(request, 'api/SCT/initiate_transfer.html', {'form': form})

