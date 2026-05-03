// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandDAOContracts is Ownable, AccessControl {
    using SafeMath for uint256;

    event Deposit(address indexed sender, uint256 amount);
    event Withdraw(address indexed sender, uint256 amount);

    uint256 public totalBalance;

    modifier onlyAdmin() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    function deposit(uint256 amount) public {
        require(amount > 0, "Deposit amount must be greater than zero");
        totalBalance = totalBalance.add(amount);
        emit Deposit(msg.sender, amount);
    }

    function withdraw(uint256 amount) public {
        require(amount > 0, "Withdrawal amount must be greater than zero");
        require(totalBalance >= amount, "Insufficient balance");
        totalBalance = totalBalance.sub(amount);
        emit Withdraw(msg.sender, amount);
    }

    function ownerChange(address newOwner) public onlyOwner {
        Ownable(newOwner);
    }
}