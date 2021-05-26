import os

import _pickle as cPickle
from steampy.client import SteamClient


class SteamClientPatched(SteamClient):

    def to_pickle(self, filename):
        with open(filename, 'wb') as file:
            cPickle.dump(self, file)

    @classmethod
    def from_pickle(cls, filename):
        try:
            with open(filename, 'rb') as file:
                a = cPickle.load(file)
        except FileNotFoundError:
            raise ValueError('The session files are not present')
        if a.is_session_alive():
            return a
        else:
            raise ValueError('The session files are corrupted or something.')
