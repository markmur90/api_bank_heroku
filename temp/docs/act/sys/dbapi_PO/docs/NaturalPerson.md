# NaturalPerson

Basic partner information

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**noncustomer** | **bool** | User already customer | [optional] 
**first_name** | **str** | First name of the user | 
**last_name** | **str** | Last name of the user | 
**date_of_birth** | **date** | Birth date of the user. In the format YYYY-MM-DD. | 

## Example

```python
from openapi_client.models.natural_person import NaturalPerson

# TODO update the JSON string below
json = "{}"
# create an instance of NaturalPerson from a JSON string
natural_person_instance = NaturalPerson.from_json(json)
# print the JSON string representation of the object
print(NaturalPerson.to_json())

# convert the object into a dict
natural_person_dict = natural_person_instance.to_dict()
# create an instance of NaturalPerson from a dict
natural_person_from_dict = NaturalPerson.from_dict(natural_person_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


