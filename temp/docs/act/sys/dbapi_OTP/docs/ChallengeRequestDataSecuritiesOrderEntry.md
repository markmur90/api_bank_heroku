# ChallengeRequestDataSecuritiesOrderEntry

challenge request data for requestType SECURITIES_ORDER_ENTRY

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | [default to 'challengeRequestDataSecuritiesOrderEntry']
**security_account_id** | **str** | the security account id | 
**security_id** | **str** | currently only wkn is supported | 
**quantity** | **float** | Quantity of orders to be traded | 
**activity_type** | [**OrderActivityType**](OrderActivityType.md) |  | 
**order_limit** | [**OrderLimit**](OrderLimit.md) |  | [optional] 
**add_ons** | [**OrderAddOns**](OrderAddOns.md) |  | [optional] 

## Example

```python
from openapi_client.models.challenge_request_data_securities_order_entry import ChallengeRequestDataSecuritiesOrderEntry

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeRequestDataSecuritiesOrderEntry from a JSON string
challenge_request_data_securities_order_entry_instance = ChallengeRequestDataSecuritiesOrderEntry.from_json(json)
# print the JSON string representation of the object
print(ChallengeRequestDataSecuritiesOrderEntry.to_json())

# convert the object into a dict
challenge_request_data_securities_order_entry_dict = challenge_request_data_securities_order_entry_instance.to_dict()
# create an instance of ChallengeRequestDataSecuritiesOrderEntry from a dict
challenge_request_data_securities_order_entry_from_dict = ChallengeRequestDataSecuritiesOrderEntry.from_dict(challenge_request_data_securities_order_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


