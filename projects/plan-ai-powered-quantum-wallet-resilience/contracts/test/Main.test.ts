import { ethers, Signer } from 'ethers';
import { expect } from 'chai';
import { Contract } from 'ethers';
import { Task } from 'hardhat-tasks';
import { MockERC2 } from './test/MockERC2.sol';
import { AQWRO } from './src/AQWRO.sol';
import { constants } from 'ethers';

// Define a simple ERC20 contract for testing
contract MockERC2 {
    let owner: Signer;
    let addr: string;

    constructor() {
        owner = ethers.provider.getSigner();
        addr = owner.address;
    }

    name() public pure returns (string memory) {
        return "MockERC2";
    }

    symbol() public pure returns (string memory) {
        return "MOCK";
    }

    balance(address _addr) public view returns (uint256) {
        return 1000000000000000000; // Initial balance
    }

    transfer(address _to, uint256 _value) public returns (bool) {
        // Simulate a transfer
        return true;
    }
}

describe('AQWRO', function () {
    let AQWRO: AQWRO;
    let owner: Signer;
    let user: Signer;
    let mockERC2: Contract;
    const deploymentAmount = ethers.utils.parseEther('0.001');

    beforeEach(async function () {
        // Create accounts
        owner = await ethers.getSigner();
        user = await ethers.getSigner();

        // Deploy MockERC2
        mockERC2 = await new MockERC2().deployed();

        // Deploy AQWRO
        AQWRO = await ethers.getContractFactory<AQWRO>('AQWRO').deploy();
        await AQWRO.deployed();
    });

    describe('Deployment Tests', function () {
        it('should deploy successfully', async function () {
            expect(AQWRO.address).to.not.equal(0);
        });

        it('should set the owner correctly', async function () {
            expect(await AQWRO.owner()).to.equal(owner.address);
        });
    });

    describe('Public Functions', function () {
        it('should correctly identify reentrancy vulnerability in MockERC2', async function () {
            // Simulate a reentrancy attack
            const attacker = user;
            const amount = ethers.utils.parseEther('0.01');
            const tx = await attacker.call({ from: attacker.address }, {
                functionName: 'transfer',
                args: [AQWRO.address, amount],
            });
            await tx.wait();

            // Verify that the contract reverts due to the reentrancy
            expect(await AQWRO.checkContract(mockERC2.address)).to.emit(constants.CreateEvent);
            expect(await AQWRO.checkContract(mockERC2.address)).to.revert;
        });

        it('should correctly identify integer overflow vulnerability in MockERC2', async function () {
            // Simulate an integer overflow
            const amount = ethers.utils.maxUint256();
            const tx = await AQWRO.addVulnerability(mockERC2.address, amount);
            await tx.wait();

            // Verify that the contract reverts due to the overflow
            expect(await AQWRO.checkContract(mockERC2.address)).to.emit(constants.CreateEvent);
            expect(await AQWRO.checkContract(mockERC2.address)).to.revert;
        });

        it('should correctly handle valid contract data', async function () {
            const amount = ethers.utils.parseEther('0.1');
            const tx = await AQWRO.addVulnerability(mockERC2.address, amount);
            await tx.wait();

            expect(await AQWRO.checkContract(mockERC2.address)).to.emit(constants.CreateEvent);
        });
    });

    describe('Access Control', function () {
        it('should only allow the owner to call certain functions', async function () {
            // Attempt to call a function that requires ownership
            try {
                await AQWRO.updateRiskScore(mockERC2.address, 10);
            } catch (error) {
                expect(error).to.not.be.null;
            }
        });
    });

    describe('Edge Cases and Reverts', function () {
        it('should revert if the contract address is invalid', async function () {
            const invalidAddress = '0x0000000000000000000000000000000