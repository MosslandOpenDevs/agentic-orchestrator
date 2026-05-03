import { ethers, Signer } from "ethers";
import { expect } from "chai";
import { Contract } from "ethers";
import { factory as abiFactory } from "./factories/GenesisAI.json";
import { constants } from "ethers";

// Mock Provider
const provider = new ethers.providers.JsonRpcProvider("http://localhost:8545");

// Mock Signer for testing
const privateKey = "0x..."; // Replace with a real private key for testing
const signer = new Signer(provider, privateKey);

// Mock Contract
const GenesisAI = new abiFactory({
  address: signer.address,
  abi: Contract.INTERFACE
});

describe("GenesisAI Contract Tests", function() {
  beforeEach(async function() {
    await GenesisAI.initialize();
  });

  describe("Deployment Tests", function() {
    it("Should deploy successfully", async function() {
      const deploymentResult = await GenesisAI.deploy();
      expect(deploymentResult.deployed).to.not.be.null;
    });
  });

  describe("Public Functions Tests", function() {
    it("Should correctly set the model name", async function() {
      const newName = "MyAwesomeModel";
      const result = await GenesisAI.setModuleName(newName);
      expect(result.events.ModuleNameSet.args.name).to.equal(newName);
    });

    it("Should correctly get the model name", async function() {
      const newName = "MyAwesomeModel";
      await GenesisAI.setModuleName(newName);
      const name = await GenesisAI.getModelName();
      expect(name).to.equal(newName);
    });

    it("Should correctly set the reward rate", async function() {
      const newRate = 100;
      const result = await GenesisAI.setRewardRate(newRate);
      expect(result.events.RewardRateSet.args.rate).to.equal(newRate);
    });

    it("Should correctly get the reward rate", async function() {
      const newRate = 100;
      await GenesisAI.setRewardRate(newRate);
      const rate = await GenesisAI.getRewardRate();
      expect(rate).to.equal(newRate);
    });
  });

  describe("Access Control Tests", function() {
    it("Should only allow owner to set parameters", async function() {
      // Mock owner address
      const ownerAddress = "0x..."; // Replace with a real owner address
      const ownerSigner = new Signer(provider, "0x...");

      // Set owner's address in GenesisAI
      await GenesisAI.setOwner(ownerAddress);

      // Attempt to set parameters by a non-owner
      const nonOwnerSigner = new Signer(provider, privateKey);
      const result = await GenesisAI.setModuleName("NonOwnerModel");
      expect(result.status).to.be.false;
    });

    it("Should allow owner to retrieve parameters", async function() {
      // Mock owner address
      const ownerAddress = "0x..."; // Replace with a real owner address
      const ownerSigner = new Signer(provider, "0x...");

      // Set owner's address in GenesisAI
      await GenesisAI.setOwner(ownerAddress);

      const name = await GenesisAI.getModelName();
      expect(name).to.not.be.null;
    });
  });

  describe("Edge Cases and Reverts Tests", function() {
    it("Should revert if reward rate is set to zero", async function() {
      const result = await GenesisAI.setRewardRate(0);
      expect(result.status).to.be.false;
    });

    it("Should revert if reward rate is set to a negative number", async function() {
      const result = await GenesisAI.setRewardRate(-100);
      expect(result.status).to.be.false;
    });

    it("Should revert if model name is empty string", async function() {
      const result = await GenesisAI.setModuleName("");
      expect(result.status).to.be.false;
    });

    it("Should revert if model name is longer than the maximum allowed length", async function() {
      const longName = "ThisIsALongNameThatExceedsTheMaximumLength";
      const result = await GenesisAI.setModuleName(longName);
      expect(result.status).to.be.false;
    });
  });
});