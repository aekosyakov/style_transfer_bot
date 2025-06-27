### Model IDs
* Lite: `kwaivgi/kling-v1.6-lite`
* Pro:  `kwaivgi/kling-v1.6-pro`

### Call sample (Python)
```python
from replicate import Client
rep = Client(api_token=os.getenv("REPLICATE_API_TOKEN"))
video_url = rep.run(
  "kwaivgi/kling-v1.6-pro",
  input={
    "prompt": "Gentle breeze animating hair",
    "start_image": img_url,
    "seconds": 5
  }
)
``` 