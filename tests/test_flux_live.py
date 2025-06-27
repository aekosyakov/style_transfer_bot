import os
import requests
from replicate import Client


def test_flux_live():
    """Test FLUX Kontext API with live request."""
    rep = Client(api_token=os.environ["REPLICATE_API_TOKEN"])
    img_url = "https://placekitten.com/256/256"  # small public domain
    out = rep.run(
        "black-forest-labs/flux-kontext-pro",
        input={
            "prompt": "watercolor painting",
            "image": img_url,
            "model_version": "flux-kontext-pro"
        },
    )
    r = requests.get(out)
    assert r.status_code == 200 and int(r.headers.get("content-length", 0)) > 1000


def test_kling_live():
    """Test Kling AI API with live request."""
    rep = Client(api_token=os.environ["REPLICATE_API_TOKEN"])
    img_url = "https://placekitten.com/256/256"  # small public domain
    video_url = rep.run(
        "kwaivgi/kling-v1.6-pro",
        input={
            "prompt": "Gentle breeze animating hair",
            "start_image": img_url,
            "seconds": 5
        }
    )
    r = requests.get(video_url)
    assert r.status_code == 200 and int(r.headers.get("content-length", 0)) > 10000


if __name__ == "__main__":
    # Run tests individually for manual testing
    try:
        test_flux_live()
        print("✅ FLUX test passed")
    except Exception as e:
        print(f"❌ FLUX test failed: {e}")
    
    try:
        test_kling_live()
        print("✅ Kling test passed")
    except Exception as e:
        print(f"❌ Kling test failed: {e}") 