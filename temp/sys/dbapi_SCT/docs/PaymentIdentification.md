# PaymentIdentification


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**end_to_end_id** | **str** | Unique identification assigned by the initiating party to unambiguously identify the transaction | [optional] 
**instruction_id** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.payment_identification import PaymentIdentification

# TODO update the JSON string below
json = "{}"
# create an instance of PaymentIdentification from a JSON string
payment_identification_instance = PaymentIdentification.from_json(json)
# print the JSON string representation of the object
print(PaymentIdentification.to_json())

# convert the object into a dict
payment_identification_dict = payment_identification_instance.to_dict()
# create an instance of PaymentIdentification from a dict
payment_identification_from_dict = PaymentIdentification.from_dict(payment_identification_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


