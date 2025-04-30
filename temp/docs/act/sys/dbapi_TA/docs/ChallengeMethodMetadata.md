# ChallengeMethodMetadata


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**mobile_phone_number** | **str** | The telephone number the short message is being sent to | [optional] 
**active_devices_count** | **int** | Number of active devices for this method type. | [optional] 

## Example

```python
from openapi_client.models.challenge_method_metadata import ChallengeMethodMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeMethodMetadata from a JSON string
challenge_method_metadata_instance = ChallengeMethodMetadata.from_json(json)
# print the JSON string representation of the object
print(ChallengeMethodMetadata.to_json())

# convert the object into a dict
challenge_method_metadata_dict = challenge_method_metadata_instance.to_dict()
# create an instance of ChallengeMethodMetadata from a dict
challenge_method_metadata_from_dict = ChallengeMethodMetadata.from_dict(challenge_method_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


