# llama-tools

## build and publish
1. install flit
```
pip install flit
```

2. build the dist
```
flit build
```

3. push the dist, you might need to change the version number in __init__.py. 
You would also need pypi account and api token ready.
```
flit publish
```

this might help --
create `~/.pypirc` with:
```
[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = <your-api-token-starts-with-pypi->
```