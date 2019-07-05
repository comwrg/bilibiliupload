# bilibiliupload
[![image](https://img.shields.io/pypi/v/bilibiliupload.svg)](https://pypi.org/project/bilibiliupload/)

Upload video to bilibili under command-line interface

## Installation
```
pip3 install bilibiliupload
```

## How to use
```python
from bilibiliupload import *

b = Bilibili()
b.login(...)
b.upload(...)

```
More details see [docs](https://comwrg.github.io/bilibiliupload)

## Why not log print
```python
import logging
logging.basicConfig()
```
More details see python logger docs

## Credits
* Thanks `KAAAsS` provides [Login API](http://docs.kaaass.net/showdoc/web/#/2?page_id=12)
* Refer Login API from [Dawnnnnnn/bilibili-live-tools](https://github.com/Dawnnnnnn/bilibili-live-tools), Thanks a lot

