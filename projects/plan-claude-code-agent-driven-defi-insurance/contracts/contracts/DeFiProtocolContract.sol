// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract DeFiProtocolContract is Ownable, AccessControl {
    using SafeMath for uint256;

    // State variables
    uint256 public totalSupply;
    uint256 public totalBorrowed;

    // Mapping to store user balances
    mapping(address => uint256) public userBalances;

    // Event listeners
    event Deposit(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);

    // Constructor
    constructor() {
        totalSupply = 0;
        totalBorrowed = 0;
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Deposit function
    function deposit(uint256 amount) public {
        require(amount > 0, "Deposit amount must be greater than 0");
        require(userBalances[msg.sender] == 0, "User already has a balance");

        totalSupply = totalSupply.add(amount);
        userBalances[msg.sender] = amount;
        emit Deposit(msg.sender, amount);
    }

    // Withdraw function
    function withdraw(uint256 amount) public {
        require(amount > 0, "Withdrawal amount must be greater than 0");
        require(userBalances[msg.sender] >= amount, "Insufficient balance");

        totalBorrowed = totalBorrowed.add(amount);
        userBalances[msg.sender] = userBalances[msg.sender].sub(amount);
        emit Withdraw(msg.sender, amount);
    }

    // Function to get the total supply
    function getTotalSupply() public view returns (uint256) {
        return totalSupply;
    }

    // Function to get the total borrowed
    function getTotalBorrowed() public view returns (uint256) {
        return totalBorrowed;
    }

    // Function to get user balance
    function getUserBalance(address user) public view returns (uint256) {
        return userBalances[user];
    }

    // Fallback function to prevent accidental ETH transfers
    receive() external payable {
        revert("This contract does not accept ETH");
    }
}