#!/usr/bin/python3

import pytest
import time
import brownie

def test_revoke_one_prevents_them_from_claiming(contracts, accounts, chain):
    token_contract, vesting_contract = contracts

    # set the periods in the contracts
    days = 86400
    months = 30 * days
    periods = map(lambda x: x*months, range(11))
    periods = list(periods)

    percents = [5] + ([9.5] * 10)
    percents = map(lambda x: int(x*1e4), percents)
    percents = list(percents)

    vesting_contract.setupVestingMode(periods, percents, {'from': accounts[0]})

    users = accounts[1:3]
    allocations = [(index+1) * 1000e18 for index, user in enumerate(users)] 
    allocations = map(lambda x: int(x), allocations)
    allocations = list(allocations)
    total_tokens = sum(allocations)
    token_contract.approve(vesting_contract.address, total_tokens, {'from': accounts[0]})
    vesting_contract.allotTokens(users, allocations, {'from': accounts[0]})

    startTime = int(time.time())
    vesting_contract.startVestingMode(startTime, {'from': accounts[0]})

    # print("isVestingClaimable", vesting_contract.isVestingClaimable(1))

    assert (False, 0) == vesting_contract.isVestingClaimable(0)

    chain.sleep(10)
    chain.mine(1)
    vesting_length = vesting_contract.vestInfoLength()

    def _claim(index):

        print("index", index)
        print("isVestingClaimable", vesting_contract.isVestingClaimable(index))
        print("vestInfo", vesting_contract.vestInfo())

        for user_id, user in enumerate(users):

            user_initial_balance = token_contract.balanceOf(user)
            contract_initial_balance = token_contract.balanceOf(vesting_contract)     

            vesting_contract.claimVestedTokens(index, {'from': user})

            user_final_balance = token_contract.balanceOf(user)            
            contract_final_balance = token_contract.balanceOf(vesting_contract) 

            assert user_final_balance - user_initial_balance == contract_initial_balance - contract_final_balance
            assert vesting_contract.tokensAlloted(user) == allocations[user_id]

            for j in range(0, index+1):
                # Should fail on reclaiming
                with brownie.reverts("This vest amount is already claimed"):
                    vesting_contract.claimVestedTokens(j, {'from': user})

            if index <= vesting_length - 2:
                for j in range(index + 1, vesting_length):        
                    with brownie.reverts("Not claimable at this time"):
                        vesting_contract.claimVestedTokens(j, {'from': user})

                    _, remaining_time = vesting_contract.isVestingClaimable(j)
                    assert months * (j-index) >= remaining_time
                    assert remaining_time > months * (j-index-1)

    # for index in range(vesting_length):
    _claim(0)
    chain.mine(timedelta=months)

    # revoke for 1st user
    contract_initial_balance = token_contract.balanceOf(vesting_contract)
    tokens_left = vesting_contract.tokensAlloted(users[0]) - vesting_contract.tokensClaimed(users[0])
    vesting_contract.revoke(users[0], {'from': accounts[0]})
    contract_final_balance = token_contract.balanceOf(vesting_contract)
    assert tokens_left == contract_final_balance - contract_initial_balance


def test_setup_vesting(contracts, accounts, chain):
    token_contract, vesting_contract = contracts

    # set the periods in the contracts
    days = 86400
    months = 30 * days
    periods = map(lambda x: x*months, range(11))
    periods = list(periods)

    percents = [5] + ([9.5] * 10)
    percents = map(lambda x: int(x*1e4), percents)
    percents = list(percents)

    vesting_contract.setupVestingMode(periods, percents, {'from': accounts[0]})

    users = accounts[1:3]
    allocations = [(index+1) * 1000e18 for index, user in enumerate(users)] 
    allocations = map(lambda x: int(x), allocations)
    allocations = list(allocations)
    total_tokens = sum(allocations)
    token_contract.approve(vesting_contract.address, total_tokens, {'from': accounts[0]})
    vesting_contract.allotTokens(users, allocations, {'from': accounts[0]})

    startTime = int(time.time())
    vesting_contract.startVestingMode(startTime, {'from': accounts[0]})

    # print("isVestingClaimable", vesting_contract.isVestingClaimable(1))

    assert (False, 0) == vesting_contract.isVestingClaimable(0)

    chain.sleep(10)
    chain.mine(1)
    vesting_length = vesting_contract.vestInfoLength()

    def _claim(index):

        print("index", index)
        print("isVestingClaimable", vesting_contract.isVestingClaimable(index))
        print("vestInfo", vesting_contract.vestInfo())

        for user_id, user in enumerate(users):

            user_initial_balance = token_contract.balanceOf(user)
            contract_initial_balance = token_contract.balanceOf(vesting_contract)     

            vesting_contract.claimVestedTokens(index, {'from': user})

            user_final_balance = token_contract.balanceOf(user)            
            contract_final_balance = token_contract.balanceOf(vesting_contract) 

            assert user_final_balance - user_initial_balance == contract_initial_balance - contract_final_balance
            assert vesting_contract.tokensAlloted(user) == allocations[user_id]

            for j in range(0, index+1):
                # Should fail on reclaiming
                with brownie.reverts("This vest amount is already claimed"):
                    vesting_contract.claimVestedTokens(j, {'from': user})

            if index <= vesting_length - 2:
                for j in range(index + 1, vesting_length):        
                    with brownie.reverts("Not claimable at this time"):
                        vesting_contract.claimVestedTokens(j, {'from': user})

                    _, remaining_time = vesting_contract.isVestingClaimable(j)
                    assert months * (j-index) >= remaining_time
                    assert remaining_time > months * (j-index-1)

    for index in range(vesting_length):
        _claim(index)

        chain.mine(timedelta=months)
        # chain.mine(1)

# @pytest.mark.parametrize("idx", range(5))
# def test_sample(contracts, accounts):
#     ibfr, vesting = contracts
#     assert vesting.token() == ibfr.address


# def test_approve(token, accounts):
#     token.approve(accounts[1], 10**19, {'from': accounts[0]})

#     assert token.allowance(accounts[0], accounts[1]) == 10**19


# def test_modify_approve(token, accounts):
#     token.approve(accounts[1], 10**19, {'from': accounts[0]})
#     token.approve(accounts[1], 12345678, {'from': accounts[0]})

#     assert token.allowance(accounts[0], accounts[1]) == 12345678


# def test_revoke_approve(token, accounts):
#     token.approve(accounts[1], 10**19, {'from': accounts[0]})
#     token.approve(accounts[1], 0, {'from': accounts[0]})

#     assert token.allowance(accounts[0], accounts[1]) == 0


# def test_approve_self(token, accounts):
#     token.approve(accounts[0], 10**19, {'from': accounts[0]})

#     assert token.allowance(accounts[0], accounts[0]) == 10**19


# def test_only_affects_target(token, accounts):
#     token.approve(accounts[1], 10**19, {'from': accounts[0]})

#     assert token.allowance(accounts[1], accounts[0]) == 0


# def test_returns_true(token, accounts):
#     tx = token.approve(accounts[1], 10**19, {'from': accounts[0]})

#     assert tx.return_value is True


# def test_approval_event_fires(accounts, token):
#     tx = token.approve(accounts[1], 10**19, {'from': accounts[0]})

#     assert len(tx.events) == 1
#     assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10**19]
