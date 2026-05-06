// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NFTHolderContract is Ownable, AccessControl {
    mapping(string => NFTHolder) nftRecords;

    event NFTMinted(string nftID, string holderAddress);

    struct NFTHolder {
        string name;
        string description;
        string imageURL;
        uint256 price;
    }

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    function mintNFT(string memory _nftID, string memory _holderAddress, string memory _name, string memory _description, string memory _imageURL, uint256 _price) external AccessControl {
        // Input Validation
        require(_nftID.length > 0, "NFT ID cannot be empty");
        require(_holderAddress.length > 0, "Holder address cannot be empty");
        require(_name.length > 0, "NFT Name cannot be empty");
        require(_description.length > 0, "NFT Description cannot be empty");
        require(_imageURL.length > 0, "NFT Image URL cannot be empty");
        require(_price > 0, "NFT Price must be greater than 0");

        // Create new NFT holder
        NFTHolder memory newNFT = NFTHolder({
            name: _name,
            description: _description,
            imageURL: _imageURL,
            price: _price
        });

        // Store NFT record
        nftRecords[_nftID] = newNFT;

        // Emit event
        emit NFTMinted(_nftID, _holderAddress);
    }

    function getNFTRecord(string memory _nftID) public view returns (NFTHolder memory) {
        return nftRecords[_nftID];
    }

    function transferNFT(string memory _nftID, string memory _newHolderAddress) external AccessControl{
        require(nftRecords[_nftID].price > 0, "NFT must have a price");
        // Implement transfer logic here - this is a placeholder
        // In a real implementation, you would handle the transfer of ownership
        // and potentially ETH.
        // This example just sets the new holder address.
        nftRecords[_nftID].holderAddress = _newHolderAddress;
        emit NFTMinted(_nftID, _newHolderAddress);
    }
}