# bilibiliupload
[![image](https://img.shields.io/pypi/v/bilibiliupload.svg)](https://pypi.org/project/bilibiliupload/)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fcomwrg%2Fbilibiliupload.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Fcomwrg%2Fbilibiliupload?ref=badge_shield)

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



## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fcomwrg%2Fbilibiliupload.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Fcomwrg%2Fbilibiliupload?ref=badge_large)