# sleep_pdf_scraping

Kinda hacky, most stuff is hard coded.

Works on Windows, no promises for other OS.

## Setup

To run for the first time, you will have to create an environment
and install dependencies. To do this, [first install conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).

Next, in Anaconda prompt navigate to the project directory and run:

~~~
$ conda env create -f req.yml
~~~

Then, activate the environment by running:

~~~
$ conda activate sleep_env
~~~


## Running the script:

To run the scraping script, put your pdfs in the PDFs folder
and run:

~~~
$ python extract_stats.py
~~~

The output should appear in the out.csv file.

## Notes

NOTE: One issue with viewing the output in Excel is that Excel can
sometimes interpret ranges as dates (for example, it will read 9-10
as September 10th). You can change the settings by following [these instructions](https://stackoverflow.com/questions/76615698/preventing-excel-from-interpreting-values-as-dates).

## TODO
We still need to standardize empty/NaN fields. Some are output as '-' and others as ''. Additional testing is needed to see if this works with all pdfs. 
