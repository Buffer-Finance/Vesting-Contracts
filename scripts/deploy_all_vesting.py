import os
import json
from brownie import Vesting, IBFR, accounts
from .vesting_allocations import VESTING_POOLS

accounts.add(os.environ['PK'])

def setup_vesting(ibfr_address, pool):
    validate_pool(pool)
    vesting_contract = Vesting.deploy(ibfr_address, pool['name'], {'from': accounts[0]}, publish_source=True)
    print(
        f"Vesting Contract Address for pool name {pool['name']}", vesting_contract.address)
    pool['contract_address'] = [vesting_contract.address]
    vesting_contract.setupVestingMode(
        pool['periods'],
        pool['percents'],
        {'from': accounts[0]}
    )

    users, allocations = zip(*pool['users'].items())
    # allocations = [int(amount * int(1e18)) for amount in allocations]
    token_contract = IBFR.at(ibfr_address)
    token_contract.approve(vesting_contract.address,
                           pool['total_tokens_allocated'], {'from': accounts[0]})
    vesting_contract.allotTokens(users, allocations, {'from': accounts[0]})

    startTime = pool['start_timestamp']
    vesting_contract.startVestingMode(startTime, {'from': accounts[0]})
    return pool

def validate_pool(pool):
    assert sum(pool['percents']) == int(1e6), "The percentages are not proper"
    users, allocations = zip(*pool['users'].items())
    assert sum(
        allocations) == pool['total_tokens_allocated'], "the total tokens alloted dont match"

    def is_monotonic(a):
        return a == sorted(a[::-1])
    assert is_monotonic(
        pool['periods']), "the periods are not arranged properly"
    assert len(pool['periods']) == len(pool['percents'])


def main():
    # Deploy iBFR on Testnet and paste the address here
    ibfr_address = "0x3447A5243A05e12854809FC9F362dc2a8D6544B0"
    # token_contract = IBFR.deploy({'from': accounts[0]}, publish_source=True)
    # print(VESTING_POOLS)
    deployed_pools = []
    for pool in VESTING_POOLS:
        pool = setup_vesting(ibfr_address, pool)
        deployed_pools.append(pool)

    # Serializing json 
    json_object = json.dumps(deployed_pools, indent = 4)
    
    # Writing to sample.json
    with open("vesting.json", "w") as outfile:
        outfile.write(json_object)
    print(deployed_pools)
