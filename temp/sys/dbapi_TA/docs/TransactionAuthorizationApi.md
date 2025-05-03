# openapi_client.TransactionAuthorizationApi

All URIs are relative to *https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_challenge_v2**](TransactionAuthorizationApi.md#create_challenge_v2) | **POST** /challenges | Initiate a challenge request.
[**get_challenge_methods_v2**](TransactionAuthorizationApi.md#get_challenge_methods_v2) | **GET** /challenges/methods | Returns the challenge methods usable for the customer during 2FA.
[**switch_method_v2**](TransactionAuthorizationApi.md#switch_method_v2) | **PATCH** /challenges/{id}/method | Switch the authorization method
[**verify_challenge_v2**](TransactionAuthorizationApi.md#verify_challenge_v2) | **PATCH** /challenges/{id} | Reply to a challenge request.
[**verify_push_tan_challenge_v2**](TransactionAuthorizationApi.md#verify_push_tan_challenge_v2) | **GET** /challenges/{id} | Verify a PushTAN challenge request.


# **create_challenge_v2**
> ChallengeRequest create_challenge_v2(challenge_start, correlation_id=correlation_id)

Initiate a challenge request.

This service generates a challenge request for the given method and transaction details. It returns among other details a unique id which can be used in further processing afterwards.

### Example

* OAuth Authentication (api_db_smart_access):
* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_request import ChallengeRequest
from openapi_client.models.challenge_start import ChallengeStart
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1"
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
    api_instance = openapi_client.TransactionAuthorizationApi(api_client)
    challenge_start = openapi_client.ChallengeStart() # ChallengeStart | Input parameters to start a challenge
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Initiate a challenge request.
        api_response = api_instance.create_challenge_v2(challenge_start, correlation_id=correlation_id)
        print("The response of TransactionAuthorizationApi->create_challenge_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TransactionAuthorizationApi->create_challenge_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **challenge_start** | [**ChallengeStart**](ChallengeStart.md)| Input parameters to start a challenge | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeRequest**](ChallengeRequest.md)

### Authorization

[api_db_smart_access](../README.md#api_db_smart_access), [api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | successful operation |  * location - URI of the created challenge resource <br>  |
**400** | Unsuccessful operation, returns http status 400. See &#39;example&#39; property for possible values. |  -  |
**401** | Unsuccessful operation, returns http status 401. See &#39;example&#39; property for possible values. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_challenge_methods_v2**
> ChallengeMethodsAndTypes get_challenge_methods_v2(correlation_id=correlation_id)

Returns the challenge methods usable for the customer during 2FA.

This service provides an overview of the customer's challenge methods and their respective status.

### Example

* OAuth Authentication (api_db_smart_access):
* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_methods_and_types import ChallengeMethodsAndTypes
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1"
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
    api_instance = openapi_client.TransactionAuthorizationApi(api_client)
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Returns the challenge methods usable for the customer during 2FA.
        api_response = api_instance.get_challenge_methods_v2(correlation_id=correlation_id)
        print("The response of TransactionAuthorizationApi->get_challenge_methods_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TransactionAuthorizationApi->get_challenge_methods_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeMethodsAndTypes**](ChallengeMethodsAndTypes.md)

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **switch_method_v2**
> ChallengeRequest switch_method_v2(id, switch_method, correlation_id=correlation_id)

Switch the authorization method

Switch the authorization method for a previously initiated challenge request to a different method.

### Example

* OAuth Authentication (api_db_smart_access):
* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_request import ChallengeRequest
from openapi_client.models.challenge_request_switch_method import ChallengeRequestSwitchMethod
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1"
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
    api_instance = openapi_client.TransactionAuthorizationApi(api_client)
    id = 'id_example' # str | Identifier for the challenge resource
    switch_method = openapi_client.ChallengeRequestSwitchMethod() # ChallengeRequestSwitchMethod | Authorization method
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Switch the authorization method
        api_response = api_instance.switch_method_v2(id, switch_method, correlation_id=correlation_id)
        print("The response of TransactionAuthorizationApi->switch_method_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TransactionAuthorizationApi->switch_method_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Identifier for the challenge resource | 
 **switch_method** | [**ChallengeRequestSwitchMethod**](ChallengeRequestSwitchMethod.md)| Authorization method | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeRequest**](ChallengeRequest.md)

### Authorization

[api_db_smart_access](../README.md#api_db_smart_access), [api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Unsuccessful operation, returns http status 400. See &#39;example&#39; property for possible values. |  -  |
**401** | Unsuccessful operation, returns http status 401. See &#39;example&#39; property for possible values. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **verify_challenge_v2**
> ChallengeResult verify_challenge_v2(id, challenge_response, correlation_id=correlation_id)

Reply to a challenge request.

If given the correct challenge response for a previously initiated challenge request, this service returns a proof token.

### Example

* OAuth Authentication (api_db_smart_access):
* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_response import ChallengeResponse
from openapi_client.models.challenge_result import ChallengeResult
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1"
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
    api_instance = openapi_client.TransactionAuthorizationApi(api_client)
    id = 'id_example' # str | Identifier for the challenge resource
    challenge_response = openapi_client.ChallengeResponse() # ChallengeResponse | Challenge response
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Reply to a challenge request.
        api_response = api_instance.verify_challenge_v2(id, challenge_response, correlation_id=correlation_id)
        print("The response of TransactionAuthorizationApi->verify_challenge_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TransactionAuthorizationApi->verify_challenge_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Identifier for the challenge resource | 
 **challenge_response** | [**ChallengeResponse**](ChallengeResponse.md)| Challenge response | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeResult**](ChallengeResult.md)

### Authorization

[api_db_smart_access](../README.md#api_db_smart_access), [api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  -  |
**400** | Unsuccessful operation, returns http status 400. See &#39;example&#39; property for possible values. |  -  |
**401** | Unsuccessful operation, returns http status 401. See &#39;example&#39; property for possible values. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **verify_push_tan_challenge_v2**
> ChallengeResult verify_push_tan_challenge_v2(id, correlation_id=correlation_id)

Verify a PushTAN challenge request.

This service checks the status of a previously initated challenge request identified by the given id.

### Example

* OAuth Authentication (api_db_smart_access):
* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_result import ChallengeResult
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1"
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
    api_instance = openapi_client.TransactionAuthorizationApi(api_client)
    id = 'id_example' # str | Identifier for the challenge resource
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Verify a PushTAN challenge request.
        api_response = api_instance.verify_push_tan_challenge_v2(id, correlation_id=correlation_id)
        print("The response of TransactionAuthorizationApi->verify_push_tan_challenge_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TransactionAuthorizationApi->verify_push_tan_challenge_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Identifier for the challenge resource | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeResult**](ChallengeResult.md)

### Authorization

[api_db_smart_access](../README.md#api_db_smart_access), [api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | successful operation |  * location - URI of the created challenge resource <br>  |
**400** | Unsuccessful operation, returns http status 400. See &#39;example&#39; property for possible values. |  -  |
**401** | Unsuccessful operation, returns http status 401. See &#39;example&#39; property for possible values. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

