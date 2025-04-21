# DocumentMetadata


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**document_name** | **str** | The name of the document. Must match the name of the multipart/form-data of the document data itself. | [optional] 
**document_reference_id** | **str** | ID of document image upload returned from earlier /documents call | [optional] 
**document_type** | **str** | The type of the document | 
**document_sub_type** | **str** | The sub type of the document | 

## Example

```python
from openapi_client.models.document_metadata import DocumentMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of DocumentMetadata from a JSON string
document_metadata_instance = DocumentMetadata.from_json(json)
# print the JSON string representation of the object
print(DocumentMetadata.to_json())

# convert the object into a dict
document_metadata_dict = document_metadata_instance.to_dict()
# create an instance of DocumentMetadata from a dict
document_metadata_from_dict = DocumentMetadata.from_dict(document_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


