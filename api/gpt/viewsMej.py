# Importar utilidades de cabeceras al inicio de views.py
+ from .cabeceras import build_headers, validate_headers, attach_common_headers

# Eliminar la función validate_headers previamente definida en views.py (ahora centralizada en cabeceras.py)
- def validate_headers(headers):
-     """Valida las cabeceras requeridas para las solicitudes."""
-     # ... (contenido de la función eliminado)

# Remover constantes ACCESS_TOKEN y ORIGIN de views.py (definidas en cabeceras.py o en configuración)
- ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...."  # token definido anteriormente
- ORIGIN = 'https://api.db.com'                             # URL definida anteriormente

# Reemplazar la construcción manual de cabeceras en initiate_sepa_transfer
 def initiate_sepa_transfer(request):
     if request.method == 'POST':
-        headers = {
-            'idempotency-id': request.headers.get('idempotency-id', str(uuid.uuid4())),
-            'otp': request.POST.get('otp', 'SEPA_TRANSFER_GRANT'),
-            'Correlation-Id': request.headers.get('Correlation-Id', str(uuid.uuid4())),
-            'apikey': request.headers.get('apikey'),
-            'Access-Control-Request-Method': request.headers.get('Access-Control-Request-Method'),
-            'Access-Control-Request-Headers': request.headers.get('Access-Control-Request-Headers'),
-            'x-request-id': request.headers.get('x-request-id', str(uuid.uuid4())),
-            'Cookie': request.headers.get('Cookie'),
-            'X-Frame-Options': request.headers.get('X-Frame-Options'),
-            'X-Content-Type-Options': request.headers.get('X-Content-Type-Options'),
-            'Strict-Transport-Security': request.headers.get('Strict-Transport-Security'),
-            'Accept': 'application/json'
-        }
-        validation_errors = validate_headers(headers)
+        headers = build_headers(request, external_method='POST')
+        validation_errors = validate_headers(headers)
         if validation_errors:
             return JsonResponse({'errors': validation_errors}, status=400)
         form = SepaCreditTransferForm(request.POST)
         if form.is_valid():
             validation_errors = validate_parameters(request.POST)
             if validation_errors:
                 return JsonResponse({'errors': validation_errors}, status=400)
             try:
                 transfer = form.save(commit=False)
                 # ... (lógica de guardado de la transferencia)
                 transfer.idempotency_key = headers['idempotency-id']
                 transfer.save()
                 payload = generate_sepa_json_payload(transfer)
-                headers.update({
-                    'Content-Type': 'application/json',
-                    'Authorization': f"Bearer {ACCESS_TOKEN}",
-                    'X-Requested-With': 'XMLHttpRequest',
-                    'Origin': str(ORIGIN),
-                })
+                headers = attach_common_headers(headers, external_method='POST')
                 oauth = get_oauth_session(request)
                 response = oauth.post(
                     'https://api.db.com:443/gw/dbapi/banking/transactions/v2',
                     json=payload, headers=headers
                 )
                 # ... (manejo de respuesta exitoso o de error)

# Reemplazar lógica de cabeceras en cancel_sepa_transfer
 def cancel_sepa_transfer(request, payment_id):
-    headers = {
-        'idempotency-id': request.headers.get('idempotency-id'),
-        'otp': request.headers.get('otp'),
-        'Correlation-Id': request.headers.get('Correlation-Id'),
-        'apikey': request.headers.get('apikey'),
-        'process-id': request.headers.get('process-id'),
-        'previewsignature': request.headers.get('previewsignature'),
-    }
-    validation_errors = validate_headers(headers)
+    headers = build_headers(request, external_method='DELETE')
+    validation_errors = validate_headers(headers)
     if validation_errors:
         return JsonResponse({'errors': validation_errors}, status=400)
     try:
         transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
         oauth = get_oauth_session(request)
-        headers.update({
-            'Authorization': f"Bearer {ACCESS_TOKEN}",
-            'Accept': 'application/json',
-            'X-Requested-With': 'XMLHttpRequest',
-            'Origin': str(ORIGIN),
-        })
+        headers = attach_common_headers(headers, external_method='DELETE')
         response = oauth.delete(
             f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}',
             headers=headers
         )
         # ... (manejo de respuesta, actualización de estado o error)

# Reemplazar lógica de cabeceras en retry_sepa_transfer_auth
 def retry_sepa_transfer_auth(request, payment_id):
-    headers = {
-        'idempotency-id': request.headers.get('idempotency-id'),
-        'otp': request.headers.get('otp'),
-        'Correlation-Id': request.headers.get('Correlation-Id'),
-        'apikey': request.headers.get('apikey'),
-        'process-id': request.headers.get('process-id'),
-        'previewsignature': request.headers.get('previewsignature'),
-    }
-    validation_errors = validate_headers(headers)
+    headers = build_headers(request, external_method='PATCH')
+    validation_errors = validate_headers(headers)
     if validation_errors:
         return JsonResponse({'errors': validation_errors}, status=400)
     try:
         transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
         # Validar campos obligatorios en cuerpo (action, authId)
         action = request.POST.get('action')
         auth_id = request.POST.get('authId')
         if not action or not auth_id:
             return JsonResponse({'errors': ["'action' y 'authId' son requeridos para reintentar el segundo factor."]}, status=400)
         oauth = get_oauth_session(request)
-        headers.update({
-            'Authorization': f"Bearer {ACCESS_TOKEN}",
-            'Accept': 'application/json',
-            'Content-Type': 'application/json',
-            'X-Requested-With': 'XMLHttpRequest',
-            'Origin': str(ORIGIN),
-        })
+        headers = attach_common_headers(headers, external_method='PATCH')
         payload = {
             "action": action,
             "authId": auth_id
         }
         response = oauth.patch(
             f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}',
             json=payload, headers=headers
         )
         # ... (manejo de respuesta exitosa o de error)

# Aplicar cabeceras centralizadas en check_transfer_status (añadir validación opcional)
 def check_transfer_status(request, payment_id):
     try:
         uuid.UUID(payment_id)  # Validar formato UUID de payment_id
         transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
         oauth = get_oauth_session(request)
-        headers = {
-            'idempotency-id': str(uuid.uuid4()),
-            'Accept': 'application/json',
-            'Authorization': f"Bearer {ACCESS_TOKEN}",
-            'X-Requested-With': 'XMLHttpRequest',
-            'Origin': str(ORIGIN),
-        }
-        correlation_id = request.headers.get('Correlation-Id')
-        if correlation_id:
-            headers['Correlation-Id'] = correlation_id
+        headers = build_headers(request, external_method='GET')
+        # Para consulta de estado, no se requiere OTP; ya se incluyen idempotency-id y Origin automáticamente.
+        headers = attach_common_headers(headers, external_method='GET')
         response = oauth.get(
             f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}/status',
             headers=headers
         )
         if response.status_code == 200:
             data = response.json()
             new_status = data.get('transactionStatus')
             if new_status:
                 transfer.transaction_status = new_status
                 transfer.save()
         else:
             error_message = handle_error_response(response)
-            logger.warning(f"Error consultando estado: {error_message}")
-            return HttpResponseBadRequest(error_message)
+            logger.warning(f"Error consultando estado: {error_message}")
+            return HttpResponseBadRequest(error_message)
         return render(request, 'api/GPT/transfer_status.html', {
             'transfer': transfer,
             'bank_response': response.json() if response.ok else None
         })
     except ValueError:
         return HttpResponseBadRequest("El payment_id proporcionado no es un UUID válido.")
     except Exception as e:
         ErrorResponse.objects.create(code=500, message=f"Error consultando estado: {str(e)}")
         return render(request, 'api/GPT/transfer_status.html', {'transfer': transfer, 'error': str(e)})
