import { expect } from "chai";
import { ethers } from "hardhat";

describe("MosslandDeFiMarketInsights", function () {
  let MarketInsights: any;
  let marketInsights: any;
  let owner: any;
  let addr1: any;

  beforeEach(async () => {
    const MarketInsights = await ethers.getContractFactory("MosslandDeFiMarketInsights");
    [owner, addr1] = await ethers.getSigners();
    marketInsights = await MarketInsights.deploy();
    await marketInsights.deployed();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await marketInsights.owner()).to.equal(owner.address);
    });
  });

  describe("Public Functions", function () {
    it("Should allow the owner to update sentiment analysis data", async function () {
      await marketInsights.updateSentimentAnalysisData(10, "Positive");
      const [score, sentiment] = await marketInsights.getSentimentAnalysisData();
      expect(score).to.equal(10);
      expect(sentiment).to.equal("Positive");
    });

    it("Should not allow non-owners to update sentiment analysis data", async function () {
      await expect(marketInsights.connect(addr1).updateSentimentAnalysisData(20, "Negative"))
        .to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Access Control", function () {
    it("Should allow only the owner to call restricted functions", async function () {
      await expect(marketInsights.connect(addr1).setBlockchainData(ethers.utils.formatBytes32String("Ethereum"), "0x123456789"))
        .to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Edge Cases and Reverts", function () {
    it("Should revert when setting invalid blockchain data", async function () {
      await expect(marketInsights.setBlockchainData(ethers.utils.formatBytes32String(""), "0x123456789"))
        .to.be.revertedWith("Invalid blockchain network name");
    });

    it("Should not allow updating sentiment analysis with invalid data", async function () {
      await expect(marketInsights.updateSentimentAnalysisData(-1, ""))
        .to.be.revertedWith("Invalid sentiment score or type");
    });
  });
});