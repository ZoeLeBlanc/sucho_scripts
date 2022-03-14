# SUCHO Scripts

Repository for scripts and tools for [SUCHO](https://www.sucho.org/).

### Contents

1. `failed_browsertrix_to_wayback.py`
   
Gets all failed links from a Browsertrix Crawl (hopefully you have none but likely you'll have some!), then checks if the links are in the Wayback Machine, and if not either generates a csv for the gsheets wayback service or sends them directly to the Wayback Machine.

Feel free to either clone or fork this repository, or just copy the script directly into your working directory.

To run the script, you'll need to install all required packages from the requirements.txt file. (`pip install -r requirements.txt`)

Then to run, the script you can input the following commands into your terminal:

```shell
python3 failed_browsertrix_to_wayback.py --yaml_path=<path to yaml file> --output_path=<path to output file> --get_csv --send_wayback
```

The yaml_path should point to where your yaml file is located and should look something like `./crawls/collections/NAME_OF_CRAWL/crawls/FILENAME.yaml` The output_path should point to where you want the output file to be saved. If left empty it will save to the same directory you are running this script. Finally `get_csv` and `send_wayback` are optional flags. `get_csv` will generate a csv file for the wayback gsheets service. `send_wayback` will send the links directly to the wayback service.

If you decide to use the `send_wayback` flag, you'll need to have an internet archive account and specifically their S3 configuration. Instructions for accessing your keys are available here <https://archive.org/services/docs/api/internetarchive/api.html#ia-s3-configuration> and I'm assuming that you are storing them as environment variables `INTERNET_ARCHIVE_ACCESS_KEY` and `INTERNET_ARCHIVE_SECRET_KEY` (feel free to edit the script to work with your setup though).

Thanks to Eric Kansa for sharing his scraping code <https://github.com/opencontext/sucho-data-rescue-scrape>, which I reused parts of for the calls to wayback machine.