# openapi_client.DeleteSepaCreditTransferApi

All URIs are relative to *https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer*

Method | HTTP request | Description
------------- | ------------- | -------------
[**payment_id_delete**](DeleteSepaCreditTransferApi.md#payment_id_delete) | **DELETE** /{paymentId} | Cancel the Sepa Credit Transfer


# **payment_id_delete**
> SepaCreditTransferResponse payment_id_delete(payment_id, idempotency_id, otp, correlation_id=correlation_id)

Cancel the Sepa Credit Transfer

Cancel a previously initiated Sepa Credit Transfer.

### Example

* OAuth Authentication (api_db_smart_access):
* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.sepa_credit_transfer_response import SepaCreditTransferResponse
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.DeleteSepaCreditTransferApi(api_client)
    payment_id = 'payment_id_example' # str | Payment Id of Sepa Credit Transfer
    idempotency_id = 'idempotency_id_example' # str | Unique id of the service call. Must be present during retries to avoid multiple processing of the same request
    otp = 'otp_example' # str | One time password required for SCT cancellation, you can use photo tan or push tan. In case of push tan pass otp as 'PUSHTAN'. in case of photo tan please generate otp by using transaction authorisation APIs. there you must use requestType as 'SEPA_TRANSFER_CANCELLATION'.
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Cancel the Sepa Credit Transfer
        api_response = api_instance.payment_id_delete(payment_id, idempotency_id, otp, correlation_id=correlation_id)
        print("The response of DeleteSepaCreditTransferApi->payment_id_delete:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DeleteSepaCreditTransferApi->payment_id_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **payment_id** | **str**| Payment Id of Sepa Credit Transfer | 
 **idempotency_id** | **str**| Unique id of the service call. Must be present during retries to avoid multiple processing of the same request | 
 **otp** | **str**| One time password required for SCT cancellation, you can use photo tan or push tan. In case of push tan pass otp as &#39;PUSHTAN&#39;. in case of photo tan please generate otp by using transaction authorisation APIs. there you must use requestType as &#39;SEPA_TRANSFER_CANCELLATION&#39;. | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**SepaCreditTransferResponse**](SepaCreditTransferResponse.md)

### Authorization

[api_db_smart_access](../README.md#api_db_smart_access), [api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Unsuccessful operation, returns http status 400. See &#39;example&#39; property for possible values. |  -  |
**401** | Unsuccessful operation, returns http status 401. See &#39;example&#39; property for possible values. |  -  |
**404** | Unsuccessful operation, returns http status 404. See &#39;example&#39; property for possible values. |  -  |
**409** | Unsuccessful operation, returns http status 409. See &#39;example&#39; property for possible values. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

