// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract TokenizedSecurityContract is Ownable, AccessControl {
    using SafeMath for uint256;

    mapping(string => TokenizedSecurity) public tokenMap;
    string public constant TOKEN_MAP_KEY = "tokenMap";

    event TokenCreated(string tokenID, string name, string ticker, uint8 decimals);
    event TokenTransferred(address from, address to, uint256 quantity, string tokenID);

    struct TokenizedSecurity {
        string name;
        string ticker;
        uint8 decimals;
        address[] holders;
    }

    constructor() {
        _setupAccessControl();
    }

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    function createToken(string memory _name, string memory _ticker, uint8 _decimals) public onlyOwner {
        require(_name.length > 0, "Token name cannot be empty");
        require(_ticker.length > 0, "Token ticker cannot be empty");
        require(_decimals > 0 && _decimals <= 24, "Decimals must be between 1 and 24");

        string memory tokenID = string(uint256(block.timestamp));

        tokenMap[tokenID] = TokenizedSecurity({
            name: _name,
            ticker: _ticker,
            decimals: _decimals,
            holders: new address[](1)
        });

        emit TokenCreated(tokenID, _name, _ticker, _decimals);
    }

    function transferToken(string memory _tokenID, address _from, address _to, uint256 _quantity) public {
        require(tokenMap[_tokenID].holders.length < 1000, "Maximum number of holders reached");

        require(_quantity > 0, "Quantity must be greater than 0");

        // Check if the sender owns the token
        require(_from != address(0), "Sender address cannot be zero");
        require(tokenMap[_tokenID].holders.length > 0, "Token must be created");
        require(tokenMap[_tokenID].holders[_from] == _from, "Sender must own the token");

        // Transfer the token
        tokenMap[_tokenID].holders[_from] = address(0);
        tokenMap[_tokenID].holders[_to] = _from;
        _quantity = _quantity.div(1000); // Adjust for decimals

        // Update the token balance at the recipient address
        // This is a simplified example and might need adjustments for complex scenarios
        // In a real-world scenario, you would likely need to update the token balance
        // in a separate storage location or use a more sophisticated mechanism.

        emit TokenTransferred(_from, _to, _quantity, _tokenID);
    }

    // Function to add a holder to the token
    function addHolder(string memory _tokenID, address _address) public onlyOwner {
        require(tokenMap[_tokenID].holders.length < 1000, "Maximum number of holders reached");
        require(_address != address(0), "Address cannot be zero");

        // Check if the address is already a holder
        require(tokenMap[_tokenID].holders.length == 0 || _address != tokenMap[_tokenID].holders[tokenMap[_tokenID].holders.length - 1], "Address already a holder");

        tokenMap[_tokenID].holders.push(_address);
        emit TokenTransferred(msg.sender, _address, 1, _tokenID);
    }
}