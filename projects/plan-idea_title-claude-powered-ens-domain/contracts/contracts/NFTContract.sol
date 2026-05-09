// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract NFTContract is Ownable, AccessControl {
    EnumerableSet<string> public nfts;
    mapping(string => NFT) public nftsMapping;

    struct NFT {
        string metadata;
        uint256 tokenId;
    }

    event NFTMinted(string nftId, string domainId, string metadata);
    event NFTMetadataUpdated(string nftId, string metadata);

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    modifier nftExists(string memory _nftId) {
        require(nftsMapping[_nftId].tokenId > 0, "NFT does not exist");
        _;
    }

    function mintNFT(string memory domainId, string memory metadata) public onlyOwner nftExists(bytes4(0x9e51436d, 0x43128731, 0x6e695797, 0x8a6d465a)) {
        // Input Validation
        require(bytes(metadata).length > 0, "Metadata cannot be empty");

        uint256 tokenId = nfts.size + 1; // Generate unique token ID
        nftsMapping[tokenId] = NFT({ metadata: metadata, tokenId: tokenId });
        nfts.add(string(tokenId));

        emit NFTMinted(string(tokenId), domainId, metadata);
    }

    function updateNFTMetadata(string memory nftId, string memory metadata) public onlyOwner nftExists(nftId) {
        // Input Validation
        require(bytes(metadata).length > 0, "Metadata cannot be empty");

        nftsMapping[nftId].metadata = metadata;

        emit NFTMetadataUpdated(nftId, metadata);
    }

    // Access Control functions
    function grantRole(address _role, address _user) public onlyOwner {
        _grantRole(_user, _role);
    }

    function revokeRole(address _role, address _user) public onlyOwner {
        _revokeRole(_user, _role);
    }
}