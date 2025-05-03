# openapi_client.ProcessingOrdersApi

All URIs are relative to *https://simulator-api.db.com:443/gw/dbapi/others/processingOrders/v2*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_processing_orders**](ProcessingOrdersApi.md#create_processing_orders) | **POST** / | Create a processing order
[**upload_document**](ProcessingOrdersApi.md#upload_document) | **POST** /documents | Upload a document image


# **create_processing_orders**
> create_processing_orders(idempotency_id, processing_order, correlation_id=correlation_id, document_data=document_data)

Create a processing order

Create a processing order. This endpoint has limited access for special consumers only. It's possible to start manual processes only.

### Example

* OAuth Authentication (api_client_credential):

```python
import openapi_client
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/processingOrders/v2
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/processingOrders/v2"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.ProcessingOrdersApi(api_client)
    idempotency_id = 'idempotency_id_example' # str | Unique id of the service call. Should be resent during retries to avoid multiple processing of the same request
    processing_order = None # bytearray | The metadata of this processing order and their belonging documents. Must be a content-type application/json and schema #/definitions/ProcessingOrderMetadata. It must be the leading part of the multipart request payload followed by the individual documents as referenced in the metadata.
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)
    document_data = None # bytearray | The document data itself. You can send multiple documents with different multipart/form-data names; valid content types are: application/pdf, image/tiff or application/xml. The number of documents must match the number of document metadata provided in JSON for multipart/form-data processingOrder.documentMetas (optional)

    try:
        # Create a processing order
        api_instance.create_processing_orders(idempotency_id, processing_order, correlation_id=correlation_id, document_data=document_data)
    except Exception as e:
        print("Exception when calling ProcessingOrdersApi->create_processing_orders: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **idempotency_id** | **str**| Unique id of the service call. Should be resent during retries to avoid multiple processing of the same request | 
 **processing_order** | **bytearray**| The metadata of this processing order and their belonging documents. Must be a content-type application/json and schema #/definitions/ProcessingOrderMetadata. It must be the leading part of the multipart request payload followed by the individual documents as referenced in the metadata. | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 
 **document_data** | **bytearray**| The document data itself. You can send multiple documents with different multipart/form-data names; valid content types are: application/pdf, image/tiff or application/xml. The number of documents must match the number of document metadata provided in JSON for multipart/form-data processingOrder.documentMetas | [optional] 

### Return type

void (empty response body)

### Authorization

[api_client_credential](../README.md#api_client_credential)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Unsuccessful operation, returns http status 400. See &#39;example&#39; property for possible values. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **upload_document**
> UploadDocumentResponse upload_document(idempotency_id, document_data, correlation_id=correlation_id)

Upload a document image

Upload a document image in advance to be used later for posting a new order. This allows to incrementally create orders with multiple and/or large documents.

### Example

* OAuth Authentication (api_client_credential):

```python
import openapi_client
from openapi_client.models.upload_document_response import UploadDocumentResponse
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/processingOrders/v2
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/processingOrders/v2"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.ProcessingOrdersApi(api_client)
    idempotency_id = 'idempotency_id_example' # str | Unique id of the service call. Should be resent during retries to avoid multiple processing of the same request
    document_data = None # bytearray | 
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Upload a document image
        api_response = api_instance.upload_document(idempotency_id, document_data, correlation_id=correlation_id)
        print("The response of ProcessingOrdersApi->upload_document:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProcessingOrdersApi->upload_document: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **idempotency_id** | **str**| Unique id of the service call. Should be resent during retries to avoid multiple processing of the same request | 
 **document_data** | **bytearray**|  | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**UploadDocumentResponse**](UploadDocumentResponse.md)

### Authorization

[api_client_credential](../README.md#api_client_credential)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: */*, application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | successful operation |  -  |
**400** | Unsuccessful operation, returns http status 400. See &#39;example&#39; property for possible values. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

