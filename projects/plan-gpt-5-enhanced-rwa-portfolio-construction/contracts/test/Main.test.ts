import { ethers, Signer } from "ethers";
import { expect } from "chai";
import { factory } from "@chainlink/contracts";
import { constants } from "ethers/constants";
import { ethers as Ethers } from "ethers";
import { solidity } from "solidity-coverage";
import { HardhatError } from "hardhat-chai";

// Mock contracts (replace with your actual contract imports)
import TerraForm from "../../src/TerraForm.sol";

describe("TerraForm", function () {
  let ethers: any;
  let Signer: any;
  let HardhatError: any;

  beforeAll(async function () {
    ethers = require("ethers");
    Signer = ethers.Signer;
    HardhatError = require("hardhat-chai").HardhatError;
  });

  const INITIAL_PRICE = 100;
  const RISK_TOLERANCE_LOW = 0.1;
  const RISK_TOLERANCE_MEDIUM = 0.3;
  const RISK_TOLERANCE_HIGH = 0.5;

  describe("Deployment Tests", function () {
    it("Should deploy successfully", async function () {
      const [owner, deployer] = await ethers.getSigners();
      const args = [
        "TerraForm",
        "0x0000000000000000000000000000000