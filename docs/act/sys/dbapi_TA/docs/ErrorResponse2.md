# ErrorResponse2

Default error response message

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** | The error code | 
**message** | **str** | Description of the belonging error code. | 
**message_id** | **str** | dbAPI internal message-id (unique identifier) that allow reference to each of your API calls. | [optional] 

## Example

```python
from openapi_client.models.error_response2 import ErrorResponse2

# TODO update the JSON string below
json = "{}"
# create an instance of ErrorResponse2 from a JSON string
error_response2_instance = ErrorResponse2.from_json(json)
# print the JSON string representation of the object
print(ErrorResponse2.to_json())

# convert the object into a dict
error_response2_dict = error_response2_instance.to_dict()
# create an instance of ErrorResponse2 from a dict
error_response2_from_dict = ErrorResponse2.from_dict(error_response2_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


