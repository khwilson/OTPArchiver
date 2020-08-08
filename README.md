# OTP Archiver

This repository sets up a GitHub action which scrapes SAMHSA's directory of Opioid Treatment Programs at some regularity. It then saves the results in the `data` folder as gzipped CSVs.

Warning: eventually, this repository will grow quite large, but at 78k-ish per daily run, it'll take about 18 years to hit 500MB, so it's more likely that this code will break in the meantime.

## Requirements

If you'd like to run locally, you can do so with Python 3.7+ and [poetry](https://python-poetry.org/). Then run

```bash
poetry install
poetry run otparchiver pull
```

## Triggering manually

First, you'll need to create a [personal access token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) with a `repo` scope. Once you have that, then you can run:

```bash
curl \
  -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token ${ACCESS_TOKEN}" \
  https://api.github.com/repos/khwilson/OTPArchiver/dispatches \
  -d '{"event_type": "manual_trigger"}'
```

## Setting the schedule

The schedule is set in the `[.github/workflows/schedule.yml](https://github.com/khwilson/OTPArchiver/blob/master/.github/workflows/schedule.yml#L4)` file. That line uses [cron syntax](https://crontab.guru/).

## Customizing

You can use this shell as is if you just change the contents of the `[pull_otps](https://github.com/khwilson/OTPArchiver/blob/master/otparchiver/cli.py#L41)` function. More generally, this whole thing is a `[click](https://click.palletsprojects.com/en/7.x/)` application, so you have all the usual tools.

Two things of note: First, the dependencies of this project are managed by `poetry`, so if you would like to change the name of the command from `otparchiver` to something more descriptive, or point to some other location, you'll need to change [this line](https://github.com/khwilson/OTPArchiver/blob/master/pyproject.toml#L20) of the `pyproject.toml`.

Second, the GitHub action [assumes](https://github.com/khwilson/OTPArchiver/blob/master/.github/workflows/schedule.yml#L46) that you're just dumping your output to the [/data] folder. You can change this by editing the `sched.yml` to say `git add SOME_OTHER_FOLDER` if you'd like.

## LICENSE

MIT
