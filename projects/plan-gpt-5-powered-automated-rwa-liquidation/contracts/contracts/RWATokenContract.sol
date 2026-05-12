// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/utils/introspection/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract RWAtoken is ERC20, Ownable {
    using SafeMath for uint256;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor(string memory _name, string memory _symbol, uint256 _initialSupply) ERC20(_name, _symbol) {
        totalSupply = _initialSupply;
        _mint(msg.sender, totalSupply);
    }

    function mint(address to, uint256 amount) public onlyOwner {
        require(to != address(0), "Cannot mint to the zero address");
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0x0), to, amount);
    }

    function burn(address to, uint256 amount) public onlyOwner {
        require(to != address(0), "Cannot burn to the zero address");
        totalSupply -= amount;
        balanceOf[to] -= amount;
        emit Transfer(address(0x0), to, amount);
    }

    function transfer(address recipient, uint256 amount) public {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        require(amount > 0, "Amount must be greater than zero");

        totalSupply -= amount;
        balanceOf[msg.sender] -= amount;
        balanceOf[recipient] += amount;
        emit Transfer(msg.sender, recipient, amount);
    }

    function approve(address token, address owner, uint256 value) public {
        require(value > 0, "Value must be greater than zero");
        _approve(token, owner, value);
    }

    function _approve(address token, address owner, uint256 value) private {
        // No need to explicitly store approved values.  ERC20 standard handles this.
    }

    receive() external payable {
        revert("This contract does not accept ETH directly.");
    }
}