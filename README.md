# Jim's Blog

## Install

```bash
export LDFLAGS="-L/usr/local/opt/zlib/lib"
export CPPFLAGS="-I/usr/local/opt/zlib/include"
poetry install
```

## Build

```text
poetry run pelican content
```

## Preview

```text
poetry run pelican --listen
```

[http://localhost:8000](http://localhost:8000)

## Deploy

```bash
poetry run make publish
poetry run make rsync_upload
```
