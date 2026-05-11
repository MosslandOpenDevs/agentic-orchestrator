// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandDeFiProtocolContract is Ownable, AccessControl {
    using SafeMath for uint256;

    // Storage Variables
    uint256 public totalBalance;
    mapping(address => uint256) public userBalances;

    // Events
    event Deposit(address user, uint256 amount);
    event Withdraw(address user, uint256 amount);

    // Constructor
    constructor() {
        totalBalance = 0;
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function.");
        _;
    }

    // Deposit function
    function deposit(uint256 amount) public {
        require(amount > 0, "Deposit amount must be greater than zero.");
        require(address(this).balance >= amount, "Insufficient balance in the protocol.");

        totalBalance = totalBalance.add(amount);
        userBalances[msg.sender] = userBalances[msg.sender].add(amount);
        emit Deposit(msg.sender, amount);
    }

    // Withdraw function
    function withdraw(uint256 amount) public {
        require(amount > 0, "Withdrawal amount must be greater than zero.");
        require(userBalances[msg.sender] >= amount, "Insufficient balance for withdrawal.");

        totalBalance = totalBalance.sub(amount);
        userBalances[msg.sender] = userBalances[msg.sender].sub(amount);
        emit Withdraw(msg.sender, amount);
    }

    // Function to get the total balance
    function getTotalBalance() public view returns (uint256) {
        return totalBalance;
    }

    // Function to get the balance of a user
    function getUserBalance(address user) public view returns (uint256) {
        return userBalances[user];
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {
        // Handle ETH receipt here if needed.  Currently, it's ignored.
    }
}