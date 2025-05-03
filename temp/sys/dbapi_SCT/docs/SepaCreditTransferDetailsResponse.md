# SepaCreditTransferDetailsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**transaction_status** | [**TransactionStatus**](TransactionStatus.md) |  | 
**payment_id** | **str** | resource identification of the generated paymentinitiation resource (&#39;Transaction-ID&#39; from the header which is populated with the Intra Bank ID); should be available at least when status is PDNG or ACCP | 
**purpose_code** | **str** | ExternalPurpose1Code | 
**requested_execution_date** | **date** | must match yyyy-MM-dd format, also in CET timezone. | 
**debtor** | [**Debtor**](Debtor.md) |  | 
**debtor_account** | [**DebtorAccount**](DebtorAccount.md) |  | 
**creditor_agent** | [**CreditorAgent**](CreditorAgent.md) |  | 
**creditor** | [**Creditor**](Creditor.md) |  | 
**creditor_account** | [**CreditorAccount**](CreditorAccount.md) |  | 
**payment_identification** | [**PaymentIdentification**](PaymentIdentification.md) |  | [optional] 
**instructed_amount** | [**InstructedAmount**](InstructedAmount.md) |  | 
**remittance_information_structured** | **str** | recommended to be used in each transaction ; contract related - references to the business; it depends on the client what they want to include | 
**remittance_information_unstructured** | **str** | recommended to be used in each transaction ; contract related : references to the business; it depends on the client what they want to include | 

## Example

```python
from openapi_client.models.sepa_credit_transfer_details_response import SepaCreditTransferDetailsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SepaCreditTransferDetailsResponse from a JSON string
sepa_credit_transfer_details_response_instance = SepaCreditTransferDetailsResponse.from_json(json)
# print the JSON string representation of the object
print(SepaCreditTransferDetailsResponse.to_json())

# convert the object into a dict
sepa_credit_transfer_details_response_dict = sepa_credit_transfer_details_response_instance.to_dict()
# create an instance of SepaCreditTransferDetailsResponse from a dict
sepa_credit_transfer_details_response_from_dict = SepaCreditTransferDetailsResponse.from_dict(sepa_credit_transfer_details_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


