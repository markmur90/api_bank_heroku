# SepaCreditTransferUpdateScaRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**action** | [**Action**](Action.md) |  | 
**auth_id** | **str** | Authentication Id used for update SCA status SEPA payment, It will be valid for 5 minutes. | 

## Example

```python
from openapi_client.models.sepa_credit_transfer_update_sca_request import SepaCreditTransferUpdateScaRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SepaCreditTransferUpdateScaRequest from a JSON string
sepa_credit_transfer_update_sca_request_instance = SepaCreditTransferUpdateScaRequest.from_json(json)
# print the JSON string representation of the object
print(SepaCreditTransferUpdateScaRequest.to_json())

# convert the object into a dict
sepa_credit_transfer_update_sca_request_dict = sepa_credit_transfer_update_sca_request_instance.to_dict()
# create an instance of SepaCreditTransferUpdateScaRequest from a dict
sepa_credit_transfer_update_sca_request_from_dict = SepaCreditTransferUpdateScaRequest.from_dict(sepa_credit_transfer_update_sca_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


