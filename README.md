# SUCHO Scripts

Repository for scripts and tools for [SUCHO](sucho.org).

Scripts:

1. `failed_browsertrix_to_wayback.py`
   Gets all failed links from a Browsertrix Crawl, checks if the links are in the Wayback Machine, and if not either generates a csv for the gsheets wayback service or sends them directly to the Wayback Machine.

To run the script, install all required packages from the requirements.txt file. (`pip install -r requirements.txt`)

Then run:

```shell
python3 failed_browsertrix_to_wayback.py --yaml_path=<path to yaml file> --output_path=<path to output file> --get_csv --send_wayback
```
The yaml_path should point to where your yaml file is located and should look something like `./crawls/collections/NAME_OF_CRAWL/crawls/FILENAME.yaml` The output_path should point to where you want the output file to be saved. If left empty it will save to the same directory you are running this script. Finally `get_csv` and `send_wayback` are optional flags. `get_csv` will generate a csv file for the wayback gsheets service. `send_wayback` will send the links directly to the wayback service.
