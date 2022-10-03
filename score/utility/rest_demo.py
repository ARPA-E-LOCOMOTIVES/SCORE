# %% [markdown]
# # REST demo
# Notebook to explore connecting to the analysis server and perform interactive analysis with SCORE
import requests
from requests.auth import AuthBase
import numpy as np
import os

import matplotlib.pyplot as plt



class TokenAuth(AuthBase):
    """Implements a custom authentication scheme."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        """Attach an API token to a custom auth header."""
        r.headers['Authorization'] = "Token " +f'{self.token}'  # Python 3.6+
        return r

# %% [markdown]
# Set the local URLS
# URL ="http://localhost:8088"
URL = "https://www.mmo-scorelocomotives.org"
URL1 = URL+"/api-token-auth/"
URL2 = URL + "/api/get_route_list/"
URL3 = URL + "/api/get_route_data/"
print(os.getcwd())

# this file is currently in the utility directory
# there is a cert file in the root (back one directory)

cert = "../arl_custom_cert_bundle.pem"

# %% [markdown]
# Get a authorization token
payload = {'username':'locomotives', 'password':'locomotives'}
t = requests.post(URL1, data=payload, verify=cert)
token = t.json().get('token')
print(token)

# %%
r = requests.get(URL2, auth=TokenAuth(token), verify=cert)
results = r.json()

# %%
print(results.get('2'))

# %%
print(URL3+'2/')
r = requests.get(URL3+'2/', auth=TokenAuth(token), verify=cert)

print(r)

# %%
route = r.json()

print(route)
# %%
