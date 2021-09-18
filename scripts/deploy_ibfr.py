import os
import json
from brownie import Vesting, IBFR, accounts

def main():
    # Deploy iBFR on Testnet and paste the address here
    token_contract = IBFR.deploy({'from': accounts[0]}, publish_source=True)

    # Serializing json 
    data = {
        "ibfr_address": token_contract.address
    }
    json_object = json.dumps(data, indent = 4)
    
    # Writing to sample.json
    with open("ibfr.json", "w") as outfile:
        outfile.write(json_object)
    print(data)
