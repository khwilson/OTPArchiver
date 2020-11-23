import csv
import datetime
import gzip
from pathlib import Path
from typing import Dict, Optional, Tuple

import bs4
import click
import requests


URL = "https://dpt2.samhsa.gov/treatment/directory.aspx"
BASE_URL = "./directory.aspx"


@click.group()
def cli():
    """ Various utilities for interacting with the SAMHSA OTP Registry """
    pass


def get_form_data_base(
    soup: bs4.BeautifulSoup,
) -> Tuple[bs4.element.Tag, Dict[str, str]]:
    form = soup.find("form", {"action": BASE_URL})
    data = {}
    data["__LASTFOCUS"] = ""
    data["__EVENTTARGET"] = ""
    data["__EVENTARGUMENT"] = ""
    data = {elt["name"]: elt["value"] for elt in form.find_all("input")}
    return form, data


@cli.command("pull")
@click.option(
    "-o",
    "--output",
    "output_filename",
    help="The location to store the resulting gzipped csv",
)
def pull_otps(output_filename: Optional[str] = None):
    """ Pull the SAMHSA OTP registry """
    if not output_filename:
        data_dir = Path("./data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True)
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        output_filename = data_dir / f"output_{today}.csv.gz"

    session = requests.session()
    click.echo("Pulling front page...")
    r = session.get(URL)
    soup = bs4.BeautifulSoup(r.content, features="html.parser")

    form, data = get_form_data_base(soup)
    select = form.find("select")
    data[select["name"]] = "0"

    click.echo("Pulling 'all' page...")
    r = session.post(URL, data=data)
    soup = bs4.BeautifulSoup(r.content, features="html.parser")
    form, data = get_form_data_base(soup)

    # get the total number of pages to iterate over by clicking the "last page"
    # link and getting the text from the final page link above the table
    data["__EVENTTARGET"] = 'ctl00$ContentPlaceHolder1$GridView1'
    data["__EVENTARGUMENT"] = 'Page$Last'

    click.echo("Loading last page of results...")
    r = session.post(URL, data=data)
    soup = bs4.BeautifulSoup(r.content, features="html.parser")

    pageCount = int(soup.find_all("table")[1].find("table").find_all("td")[-1].text)
    click.echo("There are %s pages of results to scrape..." % pageCount)


    fileHeaders = [elt.text.lower().replace(' ', '_') for elt in soup.find("tr", { "class": "HEADERSTYLE" }).find_all("th")[:-1]]
    fileHeaders.extend(['latitude', 'longitude'])
    fileData = []

    i = 1
    while i <= pageCount:
        # get page i and scrape the table
        form, data = get_form_data_base(soup)
        data["__EVENTTARGET"] = 'ctl00$ContentPlaceHolder1$GridView1'
        data["__EVENTARGUMENT"] = 'Page$' + str(i)

        click.echo("Loading page %s of results..." % i)
        r = session.post(URL, data=data)
        soup = bs4.BeautifulSoup(r.content, features="html.parser")

        trs = soup.find_all("table")[1].find_all("tr")[3:-2]

        pageData = []

        for row in trs:
            rowData = []
            for elt in row.find_all("td")[:-1]:
                # get the primary row data from the text in each td
                rowData.append(elt.text.strip('\n'))

            # get the latitude and longitude which are hidden in inputs in the phone column
            inputs = row.find_all("input")
            latitude = inputs[0].get("value")
            longitude = inputs[1].get("value")

            rowData.append(latitude)
            rowData.append(longitude)

            pageData.append(rowData)

        fileData.extend(pageData)
        i += 1

    click.echo(fileData)

    # write to file
    click.echo("Processing data...")
    soup = bs4.BeautifulSoup(r.content, features="html.parser")
    trs = soup.find("table").find_all("tr")
    headers = [elt.text for elt in trs[0].find_all("th")]
    data = [[elt.text for elt in row.find_all("td")] for row in trs[1:]]

    click.echo(f"Writing data to {output_filename}...")
    with gzip.open(output_filename, "wt") as f:
        writer = csv.writer(f)
        writer.writerow(fileHeaders)
        writer.writerows(fileData)

    click.echo("Done")


if __name__ == "__main__":
    cli()
