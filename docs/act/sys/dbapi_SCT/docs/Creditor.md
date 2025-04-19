# Creditor


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**creditor_name** | **str** | Name by which a party is known and which is usually used to identify that party | 
**creditor_postal_address** | [**Address**](Address.md) |  | [optional] 

## Example

```python
from openapi_client.models.creditor import Creditor

# TODO update the JSON string below
json = "{}"
# create an instance of Creditor from a JSON string
creditor_instance = Creditor.from_json(json)
# print the JSON string representation of the object
print(Creditor.to_json())

# convert the object into a dict
creditor_dict = creditor_instance.to_dict()
# create an instance of Creditor from a dict
creditor_from_dict = Creditor.from_dict(creditor_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


