# UploadDocumentResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**document_reference_id** | **str** | ID referencing the uploaded document, to be used in ???/orders request. | 

## Example

```python
from openapi_client.models.upload_document_response import UploadDocumentResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UploadDocumentResponse from a JSON string
upload_document_response_instance = UploadDocumentResponse.from_json(json)
# print the JSON string representation of the object
print(UploadDocumentResponse.to_json())

# convert the object into a dict
upload_document_response_dict = upload_document_response_instance.to_dict()
# create an instance of UploadDocumentResponse from a dict
upload_document_response_from_dict = UploadDocumentResponse.from_dict(upload_document_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


