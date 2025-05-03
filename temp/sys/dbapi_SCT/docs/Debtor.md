# Debtor


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**debtor_name** | **str** |  | 
**debtor_postal_address** | [**Address**](Address.md) |  | [optional] 

## Example

```python
from openapi_client.models.debtor import Debtor

# TODO update the JSON string below
json = "{}"
# create an instance of Debtor from a JSON string
debtor_instance = Debtor.from_json(json)
# print the JSON string representation of the object
print(Debtor.to_json())

# convert the object into a dict
debtor_dict = debtor_instance.to_dict()
# create an instance of Debtor from a dict
debtor_from_dict = Debtor.from_dict(debtor_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


