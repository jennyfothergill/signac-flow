#!/usr/bin/env python
"""Synchronize authors and contributor metadata.

This script synchronizes the metadata provided in the CITATION.cff
file with the zenodo metadata stored in .zenodo.json.

All authors should be listed in the CITATION.cff file, while contributors
should be listed in the contributors.yaml file. Both files use the citation
file-format.
"""
from dataclasses import dataclass

import click
import json
from ruamel.yaml import load, Loader


@dataclass
class Contributor:
    last_names: str
    first_names: str
    affiliation: str
    orcid: str = None

    @classmethod
    def from_citation_author(cls, **citation):
        return cls(
            last_names=citation.pop('family-names'),
            first_names=citation.pop('given-names'),
            **citation)

    def as_zenodo_creator(self):
        ret = dict(
            name='{} {}'.format(self.first_names, self.last_names),
            affiliation=self.affiliation)
        if self.orcid:
            ret['orcid'] = self.orcid.lstrip('https://orcid.org/')
        return ret


@click.command()
@click.option('-i', '--in-place', type=bool, is_flag=True,
              help="Modify the zenodo metadata in place.")
def sync(in_place=False):
    with open('CITATION.cff', 'rb') as file:
        citation = load(file.read(), Loader=Loader)
        authors = [
            Contributor.from_citation_author(**author)
            for author in citation['authors']]

    with open('contributors.yaml', 'rb') as file:
        citation = load(file.read(), Loader=Loader)
        contributors = [
            Contributor.from_citation_author(**contributor)
            for contributor in citation['contributors']]

    with open('.zenodo.json', 'rb') as file:
        zenodo = json.loads(file.read())
        zenodo['creators'] = [a.as_zenodo_creator() for a in authors]
        zenodo['contributors'] = [c.as_zenodo_creator() for c in contributors if c not in authors]
    if in_place:
        with open('.zenodo.json', 'wb') as file:
            file.write(json.dumps(zenodo, indent=4, sort_keys=True).encode('utf-8'))
    else:
        print(json.dumps(zenodo, indent=4, sort_keys=True))


if __name__ == '__main__':
    sync()
