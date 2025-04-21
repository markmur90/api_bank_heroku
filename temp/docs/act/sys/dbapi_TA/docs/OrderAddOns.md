# OrderAddOns

Order Add-Ons

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**expiry_date** | **date** | The expiry date defines how long the order will be valid and the order can get executed in ISO 8601 format YYYY-MM-DD | [optional] 
**restriction** | **str** | Use Order Restrictions to define specific price quote, if required. Please be aware of potential dependencies of the defined order type | [optional] 

## Example

```python
from openapi_client.models.order_add_ons import OrderAddOns

# TODO update the JSON string below
json = "{}"
# create an instance of OrderAddOns from a JSON string
order_add_ons_instance = OrderAddOns.from_json(json)
# print the JSON string representation of the object
print(OrderAddOns.to_json())

# convert the object into a dict
order_add_ons_dict = order_add_ons_instance.to_dict()
# create an instance of OrderAddOns from a dict
order_add_ons_from_dict = OrderAddOns.from_dict(order_add_ons_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


