# ChallengeResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**challenge_proof_token** | **str** | In case of a one-time/single transaction authorization it is valid once, for the current user, the provided request type and the current access_token only. The returned one-time/single transaction authorization should be treated as random string, with no structure and semantic. In case of a session transaction authorization it is time-based | [optional] 
**status** | **str** | Specifies the status | [optional] 

## Example

```python
from openapi_client.models.challenge_result import ChallengeResult

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeResult from a JSON string
challenge_result_instance = ChallengeResult.from_json(json)
# print the JSON string representation of the object
print(ChallengeResult.to_json())

# convert the object into a dict
challenge_result_dict = challenge_result_instance.to_dict()
# create an instance of ChallengeResult from a dict
challenge_result_from_dict = ChallengeResult.from_dict(challenge_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


