# infoscience-patents
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
    make -j4
    sudo make altinstall
    ```

    - https://linuxize.com/post/how-to-install-python-3-7-on-debian-9/

- Install the needed library
    - `pipenv install --python 3.7`


### Test
You may run some test by doing a :
- `pipenv run python tests.py --verbose`

## Usage

 - Before running any command, set your environnement variable :
```
export EPO_CLIENT_ID=123456
export EPO_CLIENT_SECRET=123456
```
- You have to provide the MarcXML file from Infoscience to get an update, so now we get the Infoscience database on patents :
    - connect to infoscience.epfl.ch
    - log in with advanced right (Be warned, you need be logged in Infoscience with advanced right to download the +1000 patents)
    - go to this address: `https://infoscience.epfl.ch/search?ln=en&rm=&ln=en&sf=&so=d&rg=5000&c=Infoscience&of=xm&p=980__a%3A%27patent%27`
    - assert you have more than 1'000 records, 1'000 is the limit if you are not logged
    - download the file to your disk

The path of the freshly downloaded file will be needed for the two later operations, so keep it in mind.

### Updating Infoscience patent from a XML export

- import the MarcXML file freshly downloaded with the last command and compare it with Espacenet database
    - `pipenv run python updater.py --infoscience_patents_export path_to_the_saved_export.xml`

- download the produced file in ./output into Infoscience, using this process :
    - go in infoscience.epfl.ch
    - log in with admin rights
    - click in the menu : Administration->Batch Uploader
    - Select this option in the inteface :
        - the xml file generated in ./output
        - "File type" : XML
        - "Upload mode" : --replace

#### Advanced use - Range update
- you can upload only a specific range of the patents list by doing a
    - `pipenv run python updater.py --infoscience_patents_export path_to_the_saved_export.xml --start 0 --end 200`

### Fetching for new patents for a specific year

- import the MarcXML file freshly downloaded with the last command and compare it the provided Espacenet patents from a specific year
    - `pipenv run python fetch_new.py --infoscience_patents_export path_to_the_saved_export.xml --starting_year 2015`

- download the produced file in ./output into Infoscience, using this process :
    - go in infoscience.epfl.ch
    - log in with admin rights
    - click in the menu : Administration->Batch Uploader
    - Select this option in the inteface :
        - the xml file generated in ./output
        - "File type" : XML
        - "Upload mode" : --insert
