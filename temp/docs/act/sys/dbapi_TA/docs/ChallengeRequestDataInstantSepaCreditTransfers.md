# ChallengeRequestDataInstantSepaCreditTransfers

challenge request data for requestType INSTANT_SEPA_CREDIT_TRANSFERS

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | [default to 'challengeRequestDataInstantSepaCreditTransfers']
**target_iban** | **str** | The IBAN of this account. | 
**amount_currency** | **str** | ISO 4217 Alpha 3 currency code. | 
**amount_value** | **float** | value of the money transfer in given currency | 

## Example

```python
from openapi_client.models.challenge_request_data_instant_sepa_credit_transfers import ChallengeRequestDataInstantSepaCreditTransfers

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeRequestDataInstantSepaCreditTransfers from a JSON string
challenge_request_data_instant_sepa_credit_transfers_instance = ChallengeRequestDataInstantSepaCreditTransfers.from_json(json)
# print the JSON string representation of the object
print(ChallengeRequestDataInstantSepaCreditTransfers.to_json())

# convert the object into a dict
challenge_request_data_instant_sepa_credit_transfers_dict = challenge_request_data_instant_sepa_credit_transfers_instance.to_dict()
# create an instance of ChallengeRequestDataInstantSepaCreditTransfers from a dict
challenge_request_data_instant_sepa_credit_transfers_from_dict = ChallengeRequestDataInstantSepaCreditTransfers.from_dict(challenge_request_data_instant_sepa_credit_transfers_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


