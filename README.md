# infoscience-patents (WIP)

## How it works

Fetch EPFL patents from EPO and generate MarcXML from it

## Install

- Get python3.7
    ```
    sudo apt update
    sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget libsqlite3-dev
    curl -O https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
    tar -xf Python-3.7.3.tar.xz
    cd Python-3.7.3
    ./configure --enable-optimizations --enable-loadable-sqlite-extensions
    make -j 4
    sudo make altinstall
    ```

    - https://linuxize.com/post/how-to-install-python-3-7-on-debian-9/

- `pipenv install --python 3.7`

## Usage

Before running any command, set your environnement variable :
```
export EPO_CLIENT_ID=123456
export EPO_CLIENT_SECRET=123456
```


### Test

- `pipenv run python tests.py --verbose`

### Search

Fetch patents from EPO

- `pipenv run python search.py --help`
- `pipenv run python search.py fluid`
- `pipenv run python search.py A text to search --verbose --debug`

### Synchronize

Fetch patents from Infoscience and EPO trough the provided dates (start_date and end_date arguments), then build a new MarcXML from it

- `pipenv run python sync.py --help`
- `pipenv run python sync.py --startdate 2019-01-01`
- `pipenv run python sync.py --startdate 2019-01-01 --enddate 2019-01-02 --infoscience_patents ./infoscience_patents.xml --verbose --debug`

### Loading from infoscience.epfl.ch (TO_DECIDE)

This is the default behavior.
`pipenv run python sync.py`

### Loading from a file (TO_DECIDE)

you can provide your own MarcXML file instead loading the data on Infoscience.

Example :

- get the lastest infoscience export of patents
    - `wget "https://infoscience.epfl.ch/search?ln=en&rm=&ln=en&sf=&so=d&rg=5000&c=Infoscience&of=xm&p=collection%3A%27PATENT%27" -O infoscience_patents_export.xml --header="Content-Type: text/xml"`

- import the MarcXML file freshly downloaded with the last command and compare it with Espacenet database
    - `pipenv run python sync.py --infoscience_patents ./infoscience_patents.xml`

- use the produced files found in ./output
