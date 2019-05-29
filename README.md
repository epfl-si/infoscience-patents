# infoscience-patents (WIP)

Fetch EPFL patents from EPO and generate MarcXML from it

## Install

`pipenv install --python 3.6`

## Usage

The script will fetch patents from Infoscience and EPO trough the provieded dates (start_date and end_date arguments), then build a new MarcXML from it

`pipenv run python infoscience-patents/main.py --help`

A full sample of usage :
`pipenv run python /home/del/workspace/infoscience-patents/main.py --startdate 2019-01-01 --enddate 2019-01-02 --infoscience_patents ./infoscience_patents.xml --verbose --debug`

A minimal sample of usage :
`pipenv run python /home/del/workspace/infoscience-patents/main.py --startdate 2019-01-01`

### Loading from infoscience.epfl.ch

This is the default behavior.
`pipenv run python infoscience-patents/main.py`

### Loading from a file

you can provide your own MarcXML file instead loading the data on Infoscience

Example :
`pipenv run python infoscience-patents/main.py --infoscience_patents ./infoscience_patents.xml`
