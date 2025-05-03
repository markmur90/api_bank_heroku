# ChallengeMethodItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**method** | [**ChallengeMethodType**](ChallengeMethodType.md) |  | 
**status** | **str** | Challenge method status | 
**metadata** | [**ChallengeMethodMetadata**](ChallengeMethodMetadata.md) |  | [optional] 

## Example

```python
from openapi_client.models.challenge_method_item import ChallengeMethodItem

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeMethodItem from a JSON string
challenge_method_item_instance = ChallengeMethodItem.from_json(json)
# print the JSON string representation of the object
print(ChallengeMethodItem.to_json())

# convert the object into a dict
challenge_method_item_dict = challenge_method_item_instance.to_dict()
# create an instance of ChallengeMethodItem from a dict
challenge_method_item_from_dict = ChallengeMethodItem.from_dict(challenge_method_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


