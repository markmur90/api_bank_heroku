# AddressLine


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**street_and_house_number** | **str** | Street name and house number | [optional] 
**zip_code_and_city** | **str** | Zip code and city name | [optional] 

## Example

```python
from openapi_client.models.address_line import AddressLine

# TODO update the JSON string below
json = "{}"
# create an instance of AddressLine from a JSON string
address_line_instance = AddressLine.from_json(json)
# print the JSON string representation of the object
print(AddressLine.to_json())

# convert the object into a dict
address_line_dict = address_line_instance.to_dict()
# create an instance of AddressLine from a dict
address_line_from_dict = AddressLine.from_dict(address_line_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


