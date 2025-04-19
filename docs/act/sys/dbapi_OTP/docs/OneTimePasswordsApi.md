# openapi_client.OneTimePasswordsApi

All URIs are relative to *https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_challenge_v2**](OneTimePasswordsApi.md#create_challenge_v2) | **POST** /single | Generate a one-time password challenge request.
[**get_challenge_methods_v2**](OneTimePasswordsApi.md#get_challenge_methods_v2) | **GET** / | This service returns the customers one-time-password challenge methods.
[**switch_method_v2**](OneTimePasswordsApi.md#switch_method_v2) | **PATCH** /single/{id}/switchMethod | Switch authorization method
[**verify_challenge_v2**](OneTimePasswordsApi.md#verify_challenge_v2) | **PATCH** /single/{id} | Reply to a one-time password challenge request.


# **create_challenge_v2**
> ChallengeRequest create_challenge_v2(challenge_start, correlation_id=correlation_id)

Generate a one-time password challenge request.

This service generates a one-time password challenge request for the given method and transaction.

### Example

* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_request import ChallengeRequest
from openapi_client.models.challenge_start import ChallengeStart
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.OneTimePasswordsApi(api_client)
    challenge_start = openapi_client.ChallengeStart() # ChallengeStart | Input parameters to start a OTP challenge
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Generate a one-time password challenge request.
        api_response = api_instance.create_challenge_v2(challenge_start, correlation_id=correlation_id)
        print("The response of OneTimePasswordsApi->create_challenge_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OneTimePasswordsApi->create_challenge_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **challenge_start** | [**ChallengeStart**](ChallengeStart.md)| Input parameters to start a OTP challenge | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeRequest**](ChallengeRequest.md)

### Authorization

[api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

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

This service returns the customers one-time-password challenge methods.

This service provides an overview of one-time password challenge methods and their corresponding status.

### Example

* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_methods_and_types import ChallengeMethodsAndTypes
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.OneTimePasswordsApi(api_client)
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # This service returns the customers one-time-password challenge methods.
        api_response = api_instance.get_challenge_methods_v2(correlation_id=correlation_id)
        print("The response of OneTimePasswordsApi->get_challenge_methods_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OneTimePasswordsApi->get_challenge_methods_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeMethodsAndTypes**](ChallengeMethodsAndTypes.md)

### Authorization

[api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

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
> ChallengeRequest switch_method_v2(id, challenge_response, correlation_id=correlation_id)

Switch authorization method

Switch the authorization method for a given challenge request.

### Example

* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_request import ChallengeRequest
from openapi_client.models.challenge_request_switch_method import ChallengeRequestSwitchMethod
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.OneTimePasswordsApi(api_client)
    id = 'id_example' # str | Identifier for the challenge resource
    challenge_response = openapi_client.ChallengeRequestSwitchMethod() # ChallengeRequestSwitchMethod | OTP response
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Switch authorization method
        api_response = api_instance.switch_method_v2(id, challenge_response, correlation_id=correlation_id)
        print("The response of OneTimePasswordsApi->switch_method_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OneTimePasswordsApi->switch_method_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Identifier for the challenge resource | 
 **challenge_response** | [**ChallengeRequestSwitchMethod**](ChallengeRequestSwitchMethod.md)| OTP response | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeRequest**](ChallengeRequest.md)

### Authorization

[api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

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

Reply to a one-time password challenge request.

The service generates a one-time password token, if given the correct challenge response.

### Example

* OAuth Authentication (api_auth_code):
* OAuth Authentication (api_implicit):

```python
import openapi_client
from openapi_client.models.challenge_response import ChallengeResponse
from openapi_client.models.challenge_result import ChallengeResult
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://simulator-api.db.com:443/gw/dbapi/others/onetimepasswords/v2"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.OneTimePasswordsApi(api_client)
    id = 'id_example' # str | Identifier for the challenge resource
    challenge_response = openapi_client.ChallengeResponse() # ChallengeResponse | OTP response
    correlation_id = 'correlation_id_example' # str | Free form key controlled by the caller e.g. uuid (optional)

    try:
        # Reply to a one-time password challenge request.
        api_response = api_instance.verify_challenge_v2(id, challenge_response, correlation_id=correlation_id)
        print("The response of OneTimePasswordsApi->verify_challenge_v2:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling OneTimePasswordsApi->verify_challenge_v2: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Identifier for the challenge resource | 
 **challenge_response** | [**ChallengeResponse**](ChallengeResponse.md)| OTP response | 
 **correlation_id** | **str**| Free form key controlled by the caller e.g. uuid | [optional] 

### Return type

[**ChallengeResult**](ChallengeResult.md)

### Authorization

[api_auth_code](../README.md#api_auth_code), [api_implicit](../README.md#api_implicit)

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

