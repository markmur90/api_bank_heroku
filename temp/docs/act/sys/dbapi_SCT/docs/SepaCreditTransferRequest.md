# SepaCreditTransferRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**purpose_code** | **str** | ExternalPurpose1Code | [optional] 
**requested_execution_date** | **date** | must match yyyy-MM-dd format, also in CET timezone. | [optional] 
**debtor** | [**Debtor**](Debtor.md) |  | 
**debtor_account** | [**DebtorAccount**](DebtorAccount.md) |  | 
**payment_identification** | [**PaymentIdentification**](PaymentIdentification.md) |  | [optional] 
**instructed_amount** | [**InstructedAmount**](InstructedAmount.md) |  | 
**creditor_agent** | [**CreditorAgent**](CreditorAgent.md) |  | 
**creditor** | [**Creditor**](Creditor.md) |  | 
**creditor_account** | [**CreditorAccount**](CreditorAccount.md) |  | 
**remittance_information_structured** | **str** | recommended to be used in each transaction ; contract related - references to the business; it depends on the client what they want to include | [optional] 
**remittance_information_unstructured** | **str** | recommended to be used in each transaction ; contract related : references to the business; it depends on the client what they want to include | [optional] 

## Example

```python
from openapi_client.models.sepa_credit_transfer_request import SepaCreditTransferRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SepaCreditTransferRequest from a JSON string
sepa_credit_transfer_request_instance = SepaCreditTransferRequest.from_json(json)
# print the JSON string representation of the object
print(SepaCreditTransferRequest.to_json())

# convert the object into a dict
sepa_credit_transfer_request_dict = sepa_credit_transfer_request_instance.to_dict()
# create an instance of SepaCreditTransferRequest from a dict
sepa_credit_transfer_request_from_dict = SepaCreditTransferRequest.from_dict(sepa_credit_transfer_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


