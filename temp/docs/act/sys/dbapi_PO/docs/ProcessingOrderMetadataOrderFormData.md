# ProcessingOrderMetadataOrderFormData

Structured form data associated with this processing order. The actual form elements in orderData depend on a particular form's structure, which is referenced in name/version. The form structure to be used for a given processing order will be agreed upon during on-boarding.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Order form structure (ADT) name, that defines the fields contained in orderData. | 
**version** | **int** | Order form structure (ADT) version, that defines the fields contained in orderData. | 
**product** | **str** | Product classification of this form. | 
**action** | **str** | Action sub classification of this form. | 
**data** | **Dict[str, object]** | Form content as JSON object properties with type string. The property names and values format depend on the order form structure (ADT). | 

## Example

```python
from openapi_client.models.processing_order_metadata_order_form_data import ProcessingOrderMetadataOrderFormData

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessingOrderMetadataOrderFormData from a JSON string
processing_order_metadata_order_form_data_instance = ProcessingOrderMetadataOrderFormData.from_json(json)
# print the JSON string representation of the object
print(ProcessingOrderMetadataOrderFormData.to_json())

# convert the object into a dict
processing_order_metadata_order_form_data_dict = processing_order_metadata_order_form_data_instance.to_dict()
# create an instance of ProcessingOrderMetadataOrderFormData from a dict
processing_order_metadata_order_form_data_from_dict = ProcessingOrderMetadataOrderFormData.from_dict(processing_order_metadata_order_form_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


