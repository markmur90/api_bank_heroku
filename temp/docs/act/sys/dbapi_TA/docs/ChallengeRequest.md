# ChallengeRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** | the ID of the created challenge request | 
**method** | [**ChallengeMethodType**](ChallengeMethodType.md) |  | 
**challenge** | **object** | The sub-type of the response challenge. Depending on the value see swagger model ChallengeMethodMTAN or ChallengeMethodPHOTOTAN. This is actually a constrain of the swagger 2.0 spec. | [optional] 

## Example

```python
from openapi_client.models.challenge_request import ChallengeRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeRequest from a JSON string
challenge_request_instance = ChallengeRequest.from_json(json)
# print the JSON string representation of the object
print(ChallengeRequest.to_json())

# convert the object into a dict
challenge_request_dict = challenge_request_instance.to_dict()
# create an instance of ChallengeRequest from a dict
challenge_request_from_dict = ChallengeRequest.from_dict(challenge_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


