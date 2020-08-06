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

    click.echo("Pulling second page...")
    r = session.post(URL, data=data)
    soup = bs4.BeautifulSoup(r.content, features="html.parser")
    form, data = get_form_data_base(soup)

    x = soup.find("a", {"title": "ExcelLinkButton"})["href"][
        len('javascript:__doPostBack("') :
    ]
    data["__EVENTTARGET"] = x[: x.index("'")]

    click.echo("Pulling all data....")
    r = session.post(URL, data=data)

    click.echo("Processing data...")
    soup = bs4.BeautifulSoup(r.content, features="html.parser")
    trs = soup.find("table").find_all("tr")
    headers = [elt.text for elt in trs[0].find_all("th")]
    data = [[elt.text for elt in row.find_all("td")] for row in trs[1:]]

    click.echo(f"Writing data to {output_filename}...")
    with gzip.open(output_filename, "wt") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)

    click.echo("Done")


if __name__ == "__main__":
    cli()
