This is a command line SDK for managing TDM-based dialogue domain descriptions (DDDs). For further information, see [talkamatic.se](http://talkamatic.se).

# Install dependencies
Ubuntu LTS 16.04 is supported. Install non-python dependencies with `apt-get`:
```bash
apt-get install libxml2-dev libxslt-dev libmagic1
```

# Install tala
Install the latest version of tala with pip:
```bash
pip install tala
```

# Run tala
Now run tala to get started:
```bash
tala create-ddd my_ddd
tala verify
```

For more information, consult the usage help:
```bash
tala -h
```
