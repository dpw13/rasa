import sys
from importlib import metadata

def test_tensorflow_text_install():

    try:
        metadata.metadata("tensorflow-text")
        tf_text_installed = True
    except metadata.PackageNotFoundError:
        tf_text_installed = False

    if sys.platform == "win32":
        assert not tf_text_installed
    else:
        assert tf_text_installed
