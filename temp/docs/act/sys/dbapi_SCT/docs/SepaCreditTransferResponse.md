# SepaCreditTransferResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**transaction_status** | [**TransactionStatus**](TransactionStatus.md) |  | 
**payment_id** | **str** | resource identification of the generated paymentinitiation resource (&#39;Transaction-ID&#39; from the header which is populated with the Intra Bank ID); should be available at least when status is PDNG or ACCP | 
**auth_id** | **str** | Authentication Id used for update SCA status SEPA payment, It will be valid for 5 minutes. | 

## Example

```python
from openapi_client.models.sepa_credit_transfer_response import SepaCreditTransferResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SepaCreditTransferResponse from a JSON string
sepa_credit_transfer_response_instance = SepaCreditTransferResponse.from_json(json)
# print the JSON string representation of the object
print(SepaCreditTransferResponse.to_json())

# convert the object into a dict
sepa_credit_transfer_response_dict = sepa_credit_transfer_response_instance.to_dict()
# create an instance of SepaCreditTransferResponse from a dict
sepa_credit_transfer_response_from_dict = SepaCreditTransferResponse.from_dict(sepa_credit_transfer_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


