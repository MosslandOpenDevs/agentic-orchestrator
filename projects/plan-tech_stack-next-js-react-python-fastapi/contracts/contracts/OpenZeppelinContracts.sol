// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract TokenizedNFT is Ownable, AccessControl {
    string public name = "TokenizedNFT";
    string public symbol = "TNFT";
    uint256 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => bool) public isApproved;

    event Transfer(address from, address to, uint256 amount);
    event Approval(address owner, address approved, uint256 amount);
    event Mint(address minted, uint256 amount);

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    function mint(address _to, uint256 _amount) public onlyOwner {
        require(_amount > 0, "Mint amount must be greater than zero");
        totalSupply += _amount;
        balanceOf[_to] += _amount;
        emit Mint(_to, _amount);
    }

    function transfer(address _to, uint256 _amount) public {
        require(_amount > 0, "Transfer amount must be greater than zero");
        require(balanceOf[msg.sender] >= _amount, "Insufficient balance");
        balanceOf[msg.sender] -= _amount;
        balanceOf[_to] += _amount;
        emit Transfer(msg.sender, _to, _amount);
    }

    function approve(address _to, uint256 _amount) public {
        isApproved[msg.sender] = true;
        emit Approval(msg.sender, _to, _amount);
    }

    function getOwner() public view returns (address) {
        return owner();
    }

    // Fallback function to receive ETH
    receive() external payable {}
}