# infoscience-patents (WIP)

## What it is

This project consist of two processes:

- Update the provided record from Infoscience with latest patents
- Fetch for new patents that does not exist in Infoscience

For additional information about patents and design choice, take a look at the TO_KNOW_FR.md documentation.

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

- Install the needed library
    - `pipenv install --python 3.7`

## Usage

Before running any command, set your environnement variable :
```
export EPO_CLIENT_ID=123456
export EPO_CLIENT_SECRET=123456
```

 ### Test

- `pipenv run python tests.py --verbose`

### Updating Infoscience patent from a XML export

You have to provide the MarcXML file from Infoscience to get an update.
Warning, as the limit of record per request is 1000 and there is 1'305 patents at thhis day, it is better to do in year range.

Example for the year 2016 :

- get the lastest infoscience export of patents for the 2016 year
    - `wget "https://infoscience.epfl.ch/search?ln=en&rm=&ln=en&sf=&so=d&rg=5000&c=Infoscience&of=xm&p=collection%3A'patent'+and+year%3A2016" -O infoscience_patents_2016_export.xml --header="Content-Type: text/xml"`

- import the MarcXML file freshly downloaded with the last command and compare it with Espacenet database
    - `pipenv run python updater.py --infoscience_patents ./infoscience_patents_2016_export.xml`
    -  or, to get the maximum of information, add --debug and --info
        - `pipenv run python updater.py --infoscience_patents ./infoscience_patents_2016_export.xml --debug --verbose`

- download the produced files found in ./output into the Infoscience bibedit.

### Fetching for new patents

Before fetching new patents for a specific year, you should launch an update for the year you are trying to fetch, as the updater add the family ID to the patents, and family ID are the reference used for the fetch.

- get the lastest infoscience export of patents for the 2016 year
    - `wget "https://infoscience.epfl.ch/search?ln=en&rm=&ln=en&sf=&so=d&rg=5000&c=Infoscience&of=xm&p=collection%3A'patent'+and+year%3A2016" -O infoscience_patents_2016_export.xml --header="Content-Type: text/xml"`

- import the MarcXML file freshly downloaded with the last command and compare it with Espacenet database
    - `pipenv run python fetch_new.py --infoscience_patents ./infoscience_patents_2016_export.xml --year 2016`
    -  or, to get the maximum of information, add --debug and --info
        - `pipenv run python fetch_new.py --infoscience_patents ./infoscience_patents_2016_export.xml --year 2016 --debug --verbose`

- download the produced files found in ./output into the Infoscience bibedit. This is the new records that need to be added to Infoscience
