# ProcessingOrderMetadata

The metadata of a processing order.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**created_by_system** | **str** | System identifier of the creator | 
**originating_order_id** | **str** | The internal order identification used by the originatign system. | [optional] 
**parent_processing_order_id** | **str** | The unique ID of the order | [optional] 
**processing_order_type** | **str** | The type of the order | [optional] 
**input_channel** | **str** | The input channel of the order | [optional] 
**input_originator** | **str** | The originator of this input | [optional] 
**product_group** | **str** | The product group of this order. | [optional] 
**assigned_to_group** | **str** | Group in charge | [optional] 
**processing_order_priority** | **int** | The priority of this order | [optional] 
**order_note** | **str** | additional information | [optional] 
**iban** | **str** | The IBAN of this account. | [optional] 
**partner** | [**NaturalPerson**](NaturalPerson.md) |  | [optional] 
**address** | [**Address**](Address.md) |  | [optional] 
**order_form_data** | [**ProcessingOrderMetadataOrderFormData**](ProcessingOrderMetadataOrderFormData.md) |  | [optional] 
**events** | [**List[ProcessingOrderMetadataEventsInner]**](ProcessingOrderMetadataEventsInner.md) |  | [optional] 
**document_metas** | [**List[DocumentMetadata]**](DocumentMetadata.md) |  | 

## Example

```python
from openapi_client.models.processing_order_metadata import ProcessingOrderMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessingOrderMetadata from a JSON string
processing_order_metadata_instance = ProcessingOrderMetadata.from_json(json)
# print the JSON string representation of the object
print(ProcessingOrderMetadata.to_json())

# convert the object into a dict
processing_order_metadata_dict = processing_order_metadata_instance.to_dict()
# create an instance of ProcessingOrderMetadata from a dict
processing_order_metadata_from_dict = ProcessingOrderMetadata.from_dict(processing_order_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


