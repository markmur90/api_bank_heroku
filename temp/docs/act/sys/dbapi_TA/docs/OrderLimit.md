# OrderLimit


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**limit_price** | **float** | The lowest price (for a buy) or highest price (for a sell) at which an order execution should be triggered. | [optional] 
**stop_price** | **float** |  | [optional] 

## Example

```python
from openapi_client.models.order_limit import OrderLimit

# TODO update the JSON string below
json = "{}"
# create an instance of OrderLimit from a JSON string
order_limit_instance = OrderLimit.from_json(json)
# print the JSON string representation of the object
print(OrderLimit.to_json())

# convert the object into a dict
order_limit_dict = order_limit_instance.to_dict()
# create an instance of OrderLimit from a dict
order_limit_from_dict = OrderLimit.from_dict(order_limit_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


