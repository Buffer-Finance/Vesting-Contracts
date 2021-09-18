// SPDX-License-Identifier: agpl-3.0

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License


pragma solidity ^0.8.0;

import "OpenZeppelin/openzeppelin-contracts@4.3.2/contracts/token/ERC20/ERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.3.2/contracts/token/ERC20/utils/SafeERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.3.2/contracts/utils/Address.sol";
import "OpenZeppelin/openzeppelin-contracts@4.3.2/contracts/access/Ownable.sol";

 
contract Vesting is Ownable{
    using Address for address;
    using SafeERC20 for ERC20;

    // Map user address to amount of tokens alloted //
    mapping(address => uint256) public tokensAlloted;
    mapping(address => uint256) public tokensClaimed;
    mapping(address => bool) public isRevoked;

    uint256 internal constant PERCENT100 = 1e6;

    string private _pool_name;

    struct VestingInfo {
        uint256[]  periods;
        uint256[]  percents;
        uint256 startTime;
        bool vestingTimerStarted;
    }
    VestingInfo public vestInfo;
    uint256 public vestInfoLength;
    mapping(address=>mapping(uint256=>bool)) investorsClaimMap;

    ERC20 public immutable token;

    event TokenClaimed(
        address indexed user,
        uint256 timeStamp,
        uint256 amountToken
    );

    event TokenVestingRevoked(address indexed _address, uint256 amount);

    constructor(ERC20 _token, string memory _name){
        token = _token;
        _pool_name = _name;
    }

    /**
     * @dev Setup and turn on the vesting feature
     * @param _periods - Array of period of the vesting.
     * @param _percents - Array of percents release of the vesting.
     * @notice - Access control: Public onlyOwner.
     */
    function setupVestingMode(uint256[] calldata _periods, uint256[] calldata _percents) public onlyOwner {
        
        require(!vestInfo.vestingTimerStarted, "Vesting already started");

        uint256 len = _periods.length;
        require(len>0, "Invalid length");
        require(len == _percents.length, "Wrong ranges");

        // check that all percentages should add up to 100% //
        // 100% is 1e6
        uint256 totalPcnt;
        for (uint256 n=0; n<len; n++) {
            totalPcnt = totalPcnt + _percents[n];
        }
        require(totalPcnt == PERCENT100, "Percentages add up should be 100%");
        
        vestInfoLength = len;
        vestInfo = VestingInfo({ periods:_periods, percents:_percents, startTime:0, vestingTimerStarted:false});
    }

    /**
     * @dev Allot tokens to users and transfer that many tokens to the contract
     * @param _users - Array of user addresses for alloting the tokens.
     * @param _tokenAmounts - Array of token amounts alloted to users.
     * @notice - Access control: Public onlyOwner.
     */
    function allotTokens(address[] calldata _users, uint256[] calldata _tokenAmounts) public onlyOwner {

        require(!vestInfo.vestingTimerStarted, "Vesting already started");

        uint256 len = _users.length;
        require(len>0, "Invalid length");
        require(len == _tokenAmounts.length, "Wrong ranges");

        uint256 totalAllotedAmount;

        for (uint256 n=0; n<len; n++) {
            address _user = _users[n];
            tokensAlloted[_user] += _tokenAmounts[n];
            totalAllotedAmount += _tokenAmounts[n];
        }

        token.safeTransferFrom(owner(), address(this), totalAllotedAmount);
    }

    /**
     * @dev Start the vesting counter.
     * @param startTime - Time at which the vesting will start.
     * @notice - Access control: External. onlyOwner.
     */  
    function startVestingMode(uint256 startTime) external onlyOwner {
        // Can be started only once 
        require(!vestInfo.vestingTimerStarted, "Vesting already started");

        vestInfo.startTime = startTime;
        vestInfo.vestingTimerStarted = true;
    }

    /**
     * @dev Check whether a particular vesting index has elapsed and claimable
     * @return - Bool: Claimable, uint256: If started and not claimable, returns the time needed to be claimable.
     * @notice - Access control: Public.
     */
    function isVestingClaimable(uint256 _index) public view returns(bool, uint256) {

        if (!vestInfo.vestingTimerStarted) {
            return (false,0);
        }
        uint256 period = vestInfo.periods[_index];
        uint256 releaseTime = vestInfo.startTime + period;
        bool claimable = (block.timestamp > releaseTime);
        uint256 remainTime;
        if (!claimable) {
            remainTime = releaseTime - block.timestamp; 
        }
        return (claimable, remainTime);
    }

    /**
     * @notice Allows the owner to revoke the vesting. Tokens not claimed 
     * are returned to the owner.
     * @param _user Address for which the tokens will be released
     */
    function revoke(address _user) public onlyOwner {
        require(!isRevoked[_user], "User is already revoked");

        uint256 refund = tokensAlloted[_user] - tokensClaimed[_user];
        require(refund > 0, "TokenVesting: no tokens are due");

        isRevoked[_user] = true;
        // Transfer the refundable amount back to the owner.
        token.transfer(msg.sender, refund);

        emit TokenVestingRevoked(_user, refund);
    }

    /**
     * @dev Allow users to claim their vested token, according to the index of the vested period.
     * @param _index - The index of the vesting period.
     * @notice - Access control: External.
     */  
    function claimVestedTokens(uint256 _index) external {
        
        require(!isRevoked[msg.sender], "Your tokens have been revoked");

        (bool claimable, ) = isVestingClaimable(_index);
        require(claimable, "Not claimable at this time");

        uint256 amtTotalToken = tokensAlloted[msg.sender];

        require(amtTotalToken > 0, "No tokens have been alloted to you");

        bool claimed = investorsClaimMap[msg.sender][_index];
        require(!claimed, "This vest amount is already claimed");

        investorsClaimMap[msg.sender][_index] = true;

        uint256 amtTokens = (vestInfo.percents[_index] * amtTotalToken) / PERCENT100;

        tokensClaimed[msg.sender] += amtTokens;
            
        token.safeTransfer(msg.sender, amtTokens);
        emit TokenClaimed(msg.sender, block.timestamp, amtTokens);
    }

    /**
     * @dev To get the next vesting claim for a user.
     * @param _user - The user's address.
     * @return - int256 : the next period. -1 to indicate none found.
     * @return - uint256 : the amount of token claimable
     * @return - uint256 : time left to claim. If 0 (and next claim period is valid), it is currently claimable.
     * @notice - Access control: External. View.
     */  
    function getNextVestingClaim(address _user) external view returns(int256, uint256, uint256) {

        if(isRevoked[msg.sender]){
            return (-1,0,0);
        }

        if (!vestInfo.vestingTimerStarted) {
            return (-1,0,0);
        }

        uint256 amtTotalToken = tokensAlloted[_user];
        if (amtTotalToken==0) {
            return (-1,0,0);
        }

        uint256 len = vestInfo.periods.length;
        for (uint256 n=0; n<len; n++) {
            (bool claimable, uint256 time) = isVestingClaimable(n);
            uint256 amtTokens = (vestInfo.percents[n] * amtTotalToken) / PERCENT100;
            bool claimed = investorsClaimMap[_user][n];
           
            if (!claimable) {
                return (int256(n), amtTokens, time);
            } else {
                if (!claimed) {
                    return ( int256(n), amtTokens, 0);
                }
            }
        }
        // All claimed 
        return (-1,0,0);
    }

    /**
     * @dev Returns the name of the Vesting Pool.
     */
    function pool_name() public view returns (string memory) {
        return _pool_name;
    }

    // Withdraw tokens. EMERGENCY ONLY.
    function emergencyTokenWithdraw() external onlyOwner {
        token.safeTransfer(address(msg.sender), token.balanceOf(address(this)));
    }
}