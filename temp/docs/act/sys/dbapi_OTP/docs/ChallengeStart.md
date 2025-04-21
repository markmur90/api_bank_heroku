# ChallengeStart


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**method** | [**ChallengeMethodType**](ChallengeMethodType.md) |  | 
**request_type** | **str** | The type of the OTP challenge to start. | 
**request_data** | **object** | object depending on requestType. E.g. SECURITIES_ORDER_ENTRY use model ChallengeRequestDataSecuritiesOrderEntry. | 
**language** | **str** | The language that should be used in customer facing texts created in the challenge process, i.e. SMS or photoTAN app. ISO-639-1 code. | [optional] [default to 'de']

## Example

```python
from openapi_client.models.challenge_start import ChallengeStart

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeStart from a JSON string
challenge_start_instance = ChallengeStart.from_json(json)
# print the JSON string representation of the object
print(ChallengeStart.to_json())

# convert the object into a dict
challenge_start_dict = challenge_start_instance.to_dict()
# create an instance of ChallengeStart from a dict
challenge_start_from_dict = ChallengeStart.from_dict(challenge_start_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


