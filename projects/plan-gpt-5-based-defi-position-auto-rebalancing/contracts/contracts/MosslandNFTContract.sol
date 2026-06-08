// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(string => uint256) public tokenIds;
    EnumerableSet.Controlledसत uint256[] public ownedTokens;
    event NFTMinted(address owner, string tokenId);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function mintNFT(address _owner, string memory _metadata) public onlyOwner {
        // Input Validation
        require(bytes(_metadata).length > 0, "Metadata cannot be empty");

        uint256 tokenId = tokenIds.entries().length;

        tokenIds[string(tokenId)] = tokenId;
        ownedTokens.add(tokenId);

        emit NFTMinted(_owner, string(tokenId));
    }

    function transferOwnership(address _newOwner) public onlyOwner {
        require(_newOwner != owner, "Cannot transfer ownership to yourself");
        owner = _newOwner;
        emit TransferOwnership(_newOwner);
    }

    // AccessControl functions
    function grantRole(address _target, string memory _role) public onlyOwner {
        _grantRole(_target, _role);
    }

    function revokeRole(address _target, string memory _role) public {
        _revokeRole(_target, _role);
    }

    // Helper function to get the owner
    function getOwner() public view returns (address) {
        return owner;
    }
}