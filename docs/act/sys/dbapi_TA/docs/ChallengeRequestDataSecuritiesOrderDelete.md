# ChallengeRequestDataSecuritiesOrderDelete

challenge request data for requestType SECURITIES_ORDER_DELETE

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | [default to 'challengeRequestDataSecuritiesOrderDelete']
**order_id** | **str** | Order identifier | 
**security_account_id** | **str** | the security account id | 

## Example

```python
from openapi_client.models.challenge_request_data_securities_order_delete import ChallengeRequestDataSecuritiesOrderDelete

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeRequestDataSecuritiesOrderDelete from a JSON string
challenge_request_data_securities_order_delete_instance = ChallengeRequestDataSecuritiesOrderDelete.from_json(json)
# print the JSON string representation of the object
print(ChallengeRequestDataSecuritiesOrderDelete.to_json())

# convert the object into a dict
challenge_request_data_securities_order_delete_dict = challenge_request_data_securities_order_delete_instance.to_dict()
# create an instance of ChallengeRequestDataSecuritiesOrderDelete from a dict
challenge_request_data_securities_order_delete_from_dict = ChallengeRequestDataSecuritiesOrderDelete.from_dict(challenge_request_data_securities_order_delete_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


