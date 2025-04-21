# ChallengeTypeItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | [**ChallengeTypeType**](ChallengeTypeType.md) |  | 
**metadata** | **object** | Future extension object. | [optional] 

## Example

```python
from openapi_client.models.challenge_type_item import ChallengeTypeItem

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeTypeItem from a JSON string
challenge_type_item_instance = ChallengeTypeItem.from_json(json)
# print the JSON string representation of the object
print(ChallengeTypeItem.to_json())

# convert the object into a dict
challenge_type_item_dict = challenge_type_item_instance.to_dict()
# create an instance of ChallengeTypeItem from a dict
challenge_type_item_from_dict = ChallengeTypeItem.from_dict(challenge_type_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


