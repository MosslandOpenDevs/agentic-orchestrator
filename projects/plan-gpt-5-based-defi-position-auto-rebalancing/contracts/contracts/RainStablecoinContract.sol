// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract RainStablecoinContract is Ownable, AccessControl {
    using SafeMath for uint256;

    // State Variables
    uint256 public totalSupply;
    mapping(address => uint256) public balances;

    // Event
    event Transfer(address sender, address recipient, uint256 amount);

    // Constructor
    constructor() {
        totalSupply = 0;
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    // Mint function
    function mint(uint256 amount) public onlyOwner {
        totalSupply += amount;
        balances[msg.sender] += amount;
        emit Transfer(msg.sender, address(this), amount);
    }

    // Burn function
    function burn(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        totalSupply -= amount;
        balances[msg.sender] -= amount;
        emit Transfer(msg.sender, address(this), amount);
    }

    // Transfer function (for internal use - not exposed to users)
    function _transfer(address sender, address recipient, uint256 amount) internal {
        totalSupply += amount;
        balances[sender] -= amount;
        balances[recipient] += amount;
        emit Transfer(sender, recipient, amount);
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {
        reEnteranceGuard();
    }

    // Reentrancy Guard
    function reEnteranceGuard() internal {
        require(msg.sender != address(this), "Reentrancy detected");
    }

    // Helper function to get balance
    function getBalance(address account) public view returns (uint256) {
        return balances[account];
    }
}