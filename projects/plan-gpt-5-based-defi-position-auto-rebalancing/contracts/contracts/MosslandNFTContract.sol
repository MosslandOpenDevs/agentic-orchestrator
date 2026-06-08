// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/introspection/ReentrancyGuard.sol";

contract MosslandNFTContract is Ownable, AccessControl, ReentrancyGuard {
    mapping(string => uint256) public tokenIds;
    mapping(string => address) public owners;

    string public constant NAME = "MosslandNFT";
    string public constant SYMBOL = "MNS";

    event NFTMinted(uint256 tokenId, address owner, string name, string symbol);
    event NFTTransferred(uint256 tokenId, address from, address to, address owner);

    constructor() {
        AccessControl.grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    function mintNFT(string memory _name, string memory _symbol, address _owner) external AccessControl {
        require(_name != "", "Name cannot be empty");
        require(_symbol != "", "Symbol cannot be empty");
        require(_owner != address(0), "Owner address cannot be zero");

        uint256 newTokenId = tokenIds.entries().length;
        tokenIds[stringToBytes32(_name)] = newTokenId;
        owners[_name] = _owner;

        emit NFTMinted(newTokenId, _owner, _name, _symbol);
    }

    function transferNFT(uint256 _tokenId, address _from, address _to) external AccessControl {
        require(_tokenId > 0, "Token ID must be greater than 0");
        require(tokenIds[_tokenId] > 0, "Token ID does not exist");
        require(_from != address(0), "From address cannot be zero");
        require(_to != address(0), "To address cannot be zero");
        require(owners[_tokenId] != _from, "You cannot transfer your own NFT");

        uint256 oldOwner = owners[_tokenId];
        tokenIds[_tokenId] = 0; // Mark token as transferred
        owners[_tokenId] = _to;

        emit NFTTransferred(_tokenId, _from, _to, oldOwner);
    }

    // Helper function to convert string to bytes32 for mapping key
    function stringToBytes32(string memory _str) internal pure function {
        bytes32 hash = keccak256(_str);
        return hash;
    }

    // Fallback function to prevent accidental ETH transfers
    receive() external payable {}
}