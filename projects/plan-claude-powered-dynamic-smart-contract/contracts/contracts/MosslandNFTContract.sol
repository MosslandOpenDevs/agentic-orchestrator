// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract MosslandNFTContract is Ownable, AccessControl {
    using SafeMath for uint256;

    mapping(uint256 => uint256) public tokenPrices;
    uint256 public maxSupply;
    uint256 public baseTokenId;

    event NFTMinted(uint256 tokenId, address mintedAddress);

    constructor(uint256 _maxSupply, uint256 _baseTokenId) {
        maxSupply = _maxSupply;
        baseTokenId = _baseTokenId;
    }

    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    function setTokenPrice(uint256 _tokenId, uint256 _price) external onlyOwner {
        require(_tokenId > 0 && _tokenId <= maxSupply, "Invalid token ID");
        require(_price > 0, "Price must be greater than 0");
        tokenPrices[_tokenId] = _price;
    }

    function mintNFT(uint256 tokenId) external payable {
        require(tokenId > 0 && tokenId <= maxSupply, "Invalid token ID");
        require(tokenPrices[tokenId] > 0, "Token price must be set");
        require(msg.value >= tokenPrices[tokenId], "Insufficient funds");

        // Mint the NFT
        _mint(msg.sender, tokenId);

        // Emit event
        emit NFTMinted(tokenId, msg.sender);
    }

    function transferNFT(uint256 tokenId, address to) external {
        require(tokenId > 0 && tokenId <= maxSupply, "Invalid token ID");
        require(tokenPrices[tokenId] > 0, "Token price must be set");
        require(msg.sender != to, "Sender cannot transfer to themselves");

        _transfer(msg.sender, to, tokenId);

        // Emit event
        emit NFTMinted(tokenId, to);
    }

    function _transfer(address from, address to, uint256 tokenId) internal {
        require(tokenId > 0 && tokenId <= maxSupply, "Invalid token ID");
        require(tokenPrices[tokenId] > 0, "Token price must be set");

        // Check if the sender owns the token
        require(from != address(0) && to != address(0), "Both sender and recipient must be non-zero addresses");
        require(IERC721Receiver.balanceOf(to, tokenId) == 0, "Recipient already owns this token");

        _mint(to, tokenId);
        _burn(from, tokenId);
    }

    // Helper function to mint an NFT
    function _mint(address to, uint256 tokenId) internal {
        require(tokenId > 0 && tokenId <= maxSupply, "Invalid token ID");
        _mintNFT(to, tokenId);
    }

    // Helper function to burn an NFT
    function _burn(address from, uint256 tokenId) internal {
        require(tokenId > 0 && tokenId <= maxSupply, "Invalid token ID");
        _burnNFT(from, tokenId);
    }

    // Fallback function to receive ETH
    receive() external payable {}
}

interface IERC721Receiver {
    function balanceOf(address owner, uint256 tokenID) external view returns (uint256);
    function transferFrom(address from, address to, uint256 tokenID) external returns (bool);
    function approve(address to, uint256 tokenID) external;
    function safeTransferFrom(address from, address to, uint256 tokenID) external;
    function safeTransferFrom(address from, address to, uint256 tokenID, uint256 value) external;
}