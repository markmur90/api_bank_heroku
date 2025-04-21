# ChallengeRequestDataSecuritiesOrderSession

challenge request data for requestType SECURITIES_ORDER_SESSION

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | [default to 'challengeRequestDataSecuritiesOrderSession']
**user_on_behalf_of** | **str** | UserId to send a pushTAN to in case of a technical account | [optional] 

## Example

```python
from openapi_client.models.challenge_request_data_securities_order_session import ChallengeRequestDataSecuritiesOrderSession

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeRequestDataSecuritiesOrderSession from a JSON string
challenge_request_data_securities_order_session_instance = ChallengeRequestDataSecuritiesOrderSession.from_json(json)
# print the JSON string representation of the object
print(ChallengeRequestDataSecuritiesOrderSession.to_json())

# convert the object into a dict
challenge_request_data_securities_order_session_dict = challenge_request_data_securities_order_session_instance.to_dict()
# create an instance of ChallengeRequestDataSecuritiesOrderSession from a dict
challenge_request_data_securities_order_session_from_dict = ChallengeRequestDataSecuritiesOrderSession.from_dict(challenge_request_data_securities_order_session_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


