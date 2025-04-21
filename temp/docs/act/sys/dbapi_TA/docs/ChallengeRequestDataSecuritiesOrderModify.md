# ChallengeRequestDataSecuritiesOrderModify

challenge request data for requestType SECURITIES_ORDER_MODIFY

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | [default to 'challengeRequestDataSecuritiesOrderModify']
**order_id** | **str** | Order identifier | 
**security_account_id** | **str** | the security account id | 
**order_limit** | [**OrderLimit**](OrderLimit.md) |  | [optional] 
**add_ons** | [**OrderAddOns**](OrderAddOns.md) |  | [optional] 

## Example

```python
from openapi_client.models.challenge_request_data_securities_order_modify import ChallengeRequestDataSecuritiesOrderModify

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeRequestDataSecuritiesOrderModify from a JSON string
challenge_request_data_securities_order_modify_instance = ChallengeRequestDataSecuritiesOrderModify.from_json(json)
# print the JSON string representation of the object
print(ChallengeRequestDataSecuritiesOrderModify.to_json())

# convert the object into a dict
challenge_request_data_securities_order_modify_dict = challenge_request_data_securities_order_modify_instance.to_dict()
# create an instance of ChallengeRequestDataSecuritiesOrderModify from a dict
challenge_request_data_securities_order_modify_from_dict = ChallengeRequestDataSecuritiesOrderModify.from_dict(challenge_request_data_securities_order_modify_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


