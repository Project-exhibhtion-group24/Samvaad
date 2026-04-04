// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract GrievanceRegistry {
    struct Grievance {
        string grievanceId;
        bytes32 audioHash;
        uint256 timestamp;
        address registeredBy;
    }
    
    mapping(string => Grievance) public grievances;
    string[] public grievanceIds;
    
    // Event emitted when a new grievance is registered
    event GrievanceRegistered(
        string indexed grievanceId,
        bytes32 audioHash,
        uint256 timestamp,
        address indexed registeredBy
    );
    
    /**
     * @notice Register a new grievance on the blockchain
     * @param _grievanceId The 6-digit ticket ID
     * @param _audioHash The SHA-256 hash of the audio file (as bytes32)
     */
    function registerGrievance(
        string memory _grievanceId,
        bytes32 _audioHash
    ) public {
        // Check if grievance already exists
        require(
            bytes(grievances[_grievanceId].grievanceId).length == 0,
            "Grievance ID already exists"
        );
        
        // Create new grievance record
        grievances[_grievanceId] = Grievance({
            grievanceId: _grievanceId,
            audioHash: _audioHash,
            timestamp: block.timestamp,
            registeredBy: msg.sender
        });
        
        // Add to array for enumeration
        grievanceIds.push(_grievanceId);
        
        // Emit event
        emit GrievanceRegistered(
            _grievanceId,
            _audioHash,
            block.timestamp,
            msg.sender
        );
    }
    
    /**
     * @notice Get grievance details by ID
     * @param _grievanceId The grievance ID to look up
     * @return The grievance struct
     */
    function getGrievance(string memory _grievanceId)
        public
        view
        returns (Grievance memory)
    {
        require(
            bytes(grievances[_grievanceId].grievanceId).length > 0,
            "Grievance not found"
        );
        return grievances[_grievanceId];
    }
    
    /**
     * @notice Check if a grievance exists
     * @param _grievanceId The grievance ID to check
     * @return True if grievance exists, false otherwise
     */
    function grievanceExists(string memory _grievanceId)
        public
        view
        returns (bool)
    {
        return bytes(grievances[_grievanceId].grievanceId).length > 0;
    }
    
    /**
     * @notice Get total number of registered grievances
     * @return The count of grievances
     */
    function getTotalGrievances() public view returns (uint256) {
        return grievanceIds.length;
    }
    
    /**
     * @notice Verify a grievance hash matches the stored hash
     * @param _grievanceId The grievance ID
     * @param _audioHash The hash to verify
     * @return True if hash matches, false otherwise
     */
    function verifyHash(string memory _grievanceId, bytes32 _audioHash)
        public
        view
        returns (bool)
    {
        require(
            bytes(grievances[_grievanceId].grievanceId).length > 0,
            "Grievance not found"
        );
        return grievances[_grievanceId].audioHash == _audioHash;
    }
}

