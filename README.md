# tap-awin

A singer.io tap for extracting data from the [Affiliate Window](https://www.awin.com) SOAP API written in python 3.
Author: Hugh Nimmo-Smith (hugh@onedox.com)

## Supported APIs and data models

[Affiliate Service v4](http://wiki.awin.com/index.php/Affiliate_Service_API_v4):
 - ```transactions```
 - ```merchants``` for programmes that you are joined to

## Limitations

Current limitations include:

- Only supports above data types
- No error handling
- There may be a newer (non-SOAP) API to use instead

## Configuration

The following keys are required:

```
{
  "publisher_id": 123456,
  "api_password": "<<api passeword>>",
  "user_type": "affiliate",
  "start_date": "2016-01-01",
  "validation_window": 90
}
```
