// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract AgentRegistry is Ownable, AccessControl {
    using EnumerableSet for ArrayGroupBy<address>;

    mapping(address => Agent) public agents;
    mapping(string => address) public agentNameToId;
    mapping(address => string[]) public agentIdsByAddress;

    event AgentRegistered(address agentId, string name,
                           mapping(bytes4 => bytes) metadata,
                           uint256 createdAt);

    struct Agent {
        string name;
        mapping(bytes4, bytes) metadata;
        uint256 createdAt;
    }

    EnumerableSet.ControlledInterface<address> public agentIds;

    function registerAgent(string memory _name, mapping(bytes4 => bytes) memory _metadata) external {
        require(_name.length > 0, "Agent name cannot be empty");
        require(_metadata.values.length > 0, "Agent metadata cannot be empty");

        address agentId = address(this) + getBlockNumber(); // Simple ID generation
        agents[agentId] = Agent{ _name, _metadata, block.timestamp };
        agentNameToId[_name] = agentId;
        agentIdsByAddress[agentId] = {agentId};
        agentIds.add(agentId);

        emit AgentRegistered(agentId, _name, _metadata, block.timestamp);
    }

    function getAgent(string memory _name) public view returns (
        string memory,
        mapping(bytes4 => bytes) memory,
        uint256
    ) {
        require(_name.length > 0, "Agent name cannot be empty");
        address agentId = agentNameToId[_name];
        require(agentId != address(0), "Agent not found");

        return (
            agents[agentId].name,
            agents[agentId].metadata,
            agents[agentId].createdAt
        );
    }

    function getAgentId(address _agentAddress) public view returns (address) {
        return agents[_agentAddress];
    }

    function getAgentIds() public view returns (address[] memory) {
        return agentIds.values();
    }

    // Access Control functions
    modifier onlyOwner() {
        require(msg.sender == owner(), "Only owner can call this function");
        _;
    }

    function grantRole(bytes32 _role) external onlyOwner {
        _grantRole(_role, msg.sender);
    }

    function revokeRole(bytes32 _role) external onlyOwner {
        _revokeRole(_role, msg.sender);
    }
}