# DebtorAccount


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**iban** | **str** | The IBAN of this account. | 
**currency** | **str** | ISO 4217 Alpha 3 currency code. | [optional] 

## Example

```python
from openapi_client.models.debtor_account import DebtorAccount

# TODO update the JSON string below
json = "{}"
# create an instance of DebtorAccount from a JSON string
debtor_account_instance = DebtorAccount.from_json(json)
# print the JSON string representation of the object
print(DebtorAccount.to_json())

# convert the object into a dict
debtor_account_dict = debtor_account_instance.to_dict()
# create an instance of DebtorAccount from a dict
debtor_account_from_dict = DebtorAccount.from_dict(debtor_account_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


