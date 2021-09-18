#!/usr/bin/python3

import pytest

@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def contracts(IBFR, Vesting, accounts):
    token_contract = IBFR.deploy({'from': accounts[0]})
    vesting_contract = Vesting.deploy(token_contract.address, "SeedSale", {'from': accounts[0]})
    
    return token_contract, vesting_contract
