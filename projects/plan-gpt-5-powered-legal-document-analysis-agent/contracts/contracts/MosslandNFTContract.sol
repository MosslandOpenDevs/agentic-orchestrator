// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    mapping(string => uint256) public tokenPrices;
    string public metadataURI;
    string public baseURI;

    event NFTMinted(address owner, string name, object metadata);
    event NFTTransferred(address from, address to, string tokenId);

    constructor(string _baseURI) {
        baseURI = _baseURI;
        metadataURI = _baseURI + "/1.json";
    }

    // Modifier to restrict access to only the owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    // Mint a new Mossland NFT
    function mintNFT(string memory _name, string memory _symbol, object memory _metadata) public payable {
        require(tokenPrices[_name] > 0, "Token price must be set");
        require(_metadata != "", "Metadata cannot be empty");

        uint256 tokenId = generateTokenId();
        _mint(_msgSender(), tokenId);

        // Update token price
        tokenPrices[_name] -= 1;

        // Emit event
        emit NFTMinted(_msgSender(), _name, _metadata);
    }

    // Transfer ownership of an NFT
    function transferNFT(string memory _tokenId, address _to) public {
        require(tokenPrices[_tokenId] > 0, "Token price must be set");
        require(_to != address(0), "Cannot transfer to the zero address");

        _transfer(_tokenId, _msgSender(), _to);

        // Emit event
        emit NFTTransferred(_msgSender(), _to, _tokenId);
    }

    // Helper function to generate a unique token ID
    function generateTokenId() internal pure returns (uint256) {
        return uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender.address)));
    }

    // Standard ERC-721 transfer function
    function _transfer(uint256 _tokenId, address _from, address _to) internal {
        require(_tokenId > 0, "Invalid token ID");
        require(_from != address(0), "Cannot transfer from the zero address");
        require(_to != address(0), "Cannot transfer to the zero address");

        // Check if the token is owned by the sender
        require(tokenPrices[_tokenId] > 0 && _from == _msgSender(), "Own tokens can only be transferred by the owner");

        // Transfer the token
        _safeTransfer(_from, _to, _tokenId);

        // Update token price
        tokenPrices[_tokenId] -= 1;
    }

    // Safe transfer function from OpenZeppelin
    function _safeTransfer(address _from, address _to, uint256 _tokenId) internal {
        _safeTransferHelper(_from, _to, _tokenId, 0, this);
    }

    function _safeTransferHelper(address _from, address _to, uint256 _tokenId, uint256 _offset, address _contract) internal {
        // This function is internal and should not be called externally
        // It's a helper function for _safeTransfer
    }

    // Fallback function to receive ETH
    receive() external payable {}
}