# infoscience-patents (WIP)

## How it works

Fetch EPFL patents from EPO and generate MarcXML from it


## Install

- Get python3.7
    - https://linuxize.com/post/how-to-install-python-3-7-on-debian-9/

- `pipenv install --python 3.7`

## Test

- `pipenv run python tests.py --verbose`

## Usage

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

you can provide your own MarcXML file instead loading the data on Infoscience

Example :
`pipenv run python sync.py --infoscience_patents ./infoscience_patents.xml`
