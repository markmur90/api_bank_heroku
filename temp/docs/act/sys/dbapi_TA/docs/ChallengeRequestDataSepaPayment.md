# ChallengeRequestDataSepaPayment

challenge request data for requestType for Sepa Payment transfer (SEPA_TRANSFER_GRANT, SEPA_TRANSFER_CANCELLATION)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | [default to 'challengeRequestDataSepaPaymentTransfer']
**target_iban** | **str** | The IBAN of this account. | 
**amount_currency** | **str** | ISO 4217 Alpha 3 currency code. | 
**amount_value** | **float** | value of the money transfer in given currency | 

## Example

```python
from openapi_client.models.challenge_request_data_sepa_payment import ChallengeRequestDataSepaPayment

# TODO update the JSON string below
json = "{}"
# create an instance of ChallengeRequestDataSepaPayment from a JSON string
challenge_request_data_sepa_payment_instance = ChallengeRequestDataSepaPayment.from_json(json)
# print the JSON string representation of the object
print(ChallengeRequestDataSepaPayment.to_json())

# convert the object into a dict
challenge_request_data_sepa_payment_dict = challenge_request_data_sepa_payment_instance.to_dict()
# create an instance of ChallengeRequestDataSepaPayment from a dict
challenge_request_data_sepa_payment_from_dict = ChallengeRequestDataSepaPayment.from_dict(challenge_request_data_sepa_payment_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


