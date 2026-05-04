// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RainStablecoinContract is Ownable, AccessControl {
    // Storage Variables
    float public totalSupply;
    float public decimals = 18; // Standard stablecoin decimals

    // Events
    event Mint(address indexed sender, float amount);
    event Burn(address indexed sender, float amount);

    // Constructor
    constructor() {
        totalSupply = 0.0;
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can perform this action");
        _;
    }

    // Mint Rain stablecoins
    function mint(float amount) public onlyOwner {
        require(amount > 0, "Mint amount must be greater than zero");
        require(totalSupply < 1e18, "Max supply reached"); // Prevent overflow
        totalSupply += amount;
        emit Mint(msg.sender, amount);
    }

    // Burn Rain stablecoins
    function burn(float amount) public {
        require(amount > 0, "Burn amount must be greater than zero");
        require(totalSupply >= amount, "Not enough Rain to burn");
        totalSupply -= amount;
        emit Burn(msg.sender, amount);
    }

    // Fallback function to receive ETH (reentrancy protection)
    receive() external payable {
        revert("Unsupported function: Only mint and burn are supported");
    }

    // NatSpec Documentation
    // @title RainStablecoinContract
    // @dev Manages the Rain stablecoin.
    // @note The contract uses OpenZeppelin's Ownable and AccessControl contracts for access control and event emission.
    // @param amount The amount of Rain to mint or burn.
}