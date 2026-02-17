import { expect } from "chai";
import { ethers } from "hardhat";

describe("DarkIslandsThemeContract", function () {
  let DarkIslandsTheme: any;
  let darkIslandsTheme: any;
  let owner: any;
  let addr1: any;

  beforeEach(async () => {
    const accounts = await ethers.getSigners();
    owner = accounts[0];
    addr1 = accounts[1];

    DarkIslandsTheme = await ethers.getContractFactory("DarkIslandsTheme");
    darkIslandsTheme = await DarkIslandsTheme.deploy();
    await darkIslandsTheme.deployed();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await darkIslandsTheme.owner()).to.equal(owner.address);
    });
  });

  describe("Public Functions", function () {
    it("Allows setting theme color by owner", async function () {
      await darkIslandsTheme.connect(owner).setThemeColor("#00FF00");
      expect(await darkIslandsTheme.themeColor()).to.equal("#00FF00");
    });

    it("Reverts when non-owner tries to set theme color", async function () {
      await expect(
        darkIslandsTheme.connect(addr1).setThemeColor("#00FF00")
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Edge Cases and Reverts", function () {
    it("Reverts when setting an invalid theme color", async function () {
      await expect(
        darkIslandsTheme.connect(owner).setThemeColor("#00FF")
      ).to.be.revertedWith("Invalid color format");
    });
  });
});