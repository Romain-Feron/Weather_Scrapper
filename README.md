# 0- Prerequisite
 - python 3.6 or above installed.
 - Check if pip is installed. Run `pip --version` to check that. (If not installed, install
    it via `python -m pip install pip`)

# 1- Install deps
From the app folder, run in the command line prompt `pip install -r requirements.txt` 

# 2- Check the browser version
On EdgeChromium open the `3-do menu` > `Settings` > `About Microsoft Edge`
and copy the version (Should be something like '112.0.1722.39')

# 3- Download driver
Go on https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/ 
and search the version on your EdgeChromium Browser, download it depending on
the system version

# 4- Add the driver to app
Copy the driver from archive file into the `<CURRENT_DIRECTORY>/drivers` folder.
The driver name should be exactly `msedgedriver.exe`.

# 5- Start the app
Scrap the data using, in the command line,`python weather_scrap.py [OPTIONS] <location>`
with the needed options:
 - `-s`, `--start`: Date to start the scraper, **required** to start the app.
 - `-e`, `--end`: Date to end the scraper. If not provided, `now` will be used as end date.
 - `-d`, `--days`: Number of days to get data for. Should not be used if using the end date.
 - `-o`, `--output`: File to save the scraped data. If not provided, the filename will be the
    concatenation of the location, the start date and the end date with `csv` extension.

# (6- Averaging the data)
If needed and because we scrap the data twice an hour, you can average the data for a file
using the command line with `python avg_by_hour.py <file_to_avg>`. The data will then be averaged
for a 366-days year, so be sure it's what you want (Mainly if more than one year have been scraped).