import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

# Global cache for reputation data
reputation_cache = {}
CACHE_EXPIRY_SECONDS = 300  # 5 minutes for cache validity

def normalize_reputation_identifier(identifier: str) -> str:
    """
    Normalize reputation score identifiers to match the format used in the database.
    Handles common variations of entity names.
    """
    if not identifier:
        return identifier
    
    # Convert to lowercase for case-insensitive matching
    identifier = identifier.lower()
    
    # Handle specific name mappings
    name_mappings = {
        # Handle variations of DecentraGov DAO
        "decentragov_dao": "decentra_dao",
        "decentragov": "decentra_dao",
        "decentra_gov_dao": "decentra_dao",
        "decentrag_dao": "decentra_dao",
        
        # Handle variations of Alex Rodriguez
        "alex_rodriguez": "alex_developer",
        "alex": "alex_developer",
        "rodriguez": "alex_developer",
    }
    
    # Return the mapped identifier if it exists, otherwise return the original
    return name_mappings.get(identifier, identifier)

async def fetch_reputation_score(identifier: str, query_details: Optional[str], timestamp: str) -> Dict[str, Any]:
    """
    Fetches and verifies reputation and trust scores for entities (users, services, DAOs).
    
    In a real implementation, this would aggregate from multiple decentralized reputation
    systems and provide cryptographically verifiable proofs.
    """
    # Normalize the identifier to handle variations
    normalized_identifier = normalize_reputation_identifier(identifier)
    
    # Simulated reputation database with different user types - we need this first to detect entity type
    simulated_reputation_data = {
        "alex_developer": {
            "general": {
                "name": "Alex Rodriguez",
                "did": "did:fetch:alex_developer",
                "overallScore": 92,  # Out of 100
                "activeScoreProof": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",  # IPFS CID for proof (simulated)
                "contributionStats": {
                    "totalContributions": 215,
                    "projectsContributed": 12,
                    "firstContribution": "2021-02-18"
                },
                "reputationBreakdown": {
                    "codeQuality": 95,
                    "projectCompletion": 90,
                    "communityEngagement": 88,
                    "documentation": 85
                },
                "topSkills": ["Rust", "Smart Contracts", "Agent Development"],
                "verificationMethod": "Multi-Source Attestation",
                "attesters": ["GitHub", "Fetch.ai Network", "DevDAO"]
            },
            "developer": {
                "name": "Alex Rodriguez",
                "did": "did:fetch:alex_developer",
                "developerScore": 95,  # Developer-specific score
                "codeStats": {
                    "repositories": 32,
                    "pullRequests": 287,
                    "codeReviews": 342,
                    "issuesClosed": 156
                },
                "languages": [
                    {"name": "Rust", "proficiency": 98},
                    {"name": "Python", "proficiency": 92},
                    {"name": "Solidity", "proficiency": 88}
                ],
                "significantProjects": [
                    {"name": "Agent Framework Extension", "role": "Lead Developer", "impact": "High"},
                    {"name": "Smart Contract Auditing Tool", "role": "Contributor", "impact": "Medium"}
                ],
                "verificationMethod": "Code Repository Analysis + Peer Attestation",
                "attesters": ["GitHub", "GitLab", "Code Review DAO"]
            }
        },
        "decentra_dao": {
            "general": {
                "name": "DecentraGov DAO",
                "did": "did:fetch:decentra_dao",
                "overallScore": 89,
                "activeScoreProof": "bafybeihkqhjuk6bnlr6xmqkxheh4oewvqllzwgv3vdgdsfyqgd6d2hld7e",
                "governanceStats": {
                    "members": 1250,
                    "proposalsCreated": 87,
                    "votingParticipation": "68%",
                    "treasurySize": "485,000 USDC"
                },
                "reputationBreakdown": {
                    "transparency": 94,
                    "proposalExecution": 87,
                    "communityEngagement": 91,
                    "fundManagement": 85
                },
                "verificationMethod": "On-Chain Governance Analysis",
                "attesters": ["DAOstats", "Governance Observer", "Blockchain Analytics Network"]
            },
            "contributor": {
                "name": "DecentraGov DAO",
                "did": "did:fetch:decentra_dao",
                "contributorReputation": 91,
                "contributionStats": {
                    "activeDuration": "2.5 years",
                    "contributorsReward": "Fair (verified)",
                    "onboardingQuality": "Excellent",
                    "retentionRate": "78%"
                },
                "significantContributions": [
                    {"name": "Open Source AI Model", "type": "Technology", "impact": "High"},
                    {"name": "Governance Framework", "type": "Protocol", "impact": "Medium"}
                ],
                "verificationMethod": "Contributor Experience Verification",
                "attesters": ["ContributorBoard", "WorkDAO", "Open Source Alliance"]
            }
        },
        "trustdata_service": {
            "general": {
                "name": "TrustData Verification Service",
                "did": "did:fetch:trustdata_service",
                "overallScore": 96,
                "activeScoreProof": "bafybeiczsscdsbs7ffqz55asqdf3smv6klcw3gofszvwlyarci47bgf354",
                "serviceStats": {
                    "uptime": "99.98%",
                    "users": 12850,
                    "launchDate": "2022-05-15",
                    "verifiedTransactions": 1287650
                },
                "reputationBreakdown": {
                    "reliability": 98,
                    "accuracy": 97,
                    "security": 95,
                    "support": 92
                },
                "verificationMethod": "Service Quality Attestation",
                "attesters": ["ServiceRating DAO", "User Feedback Oracle", "Security Audit Collective"]
            },
            "service": {
                "name": "TrustData Verification Service",
                "did": "did:fetch:trustdata_service",
                "serviceScore": 97,
                "performanceMetrics": {
                    "responseTime": "0.3 seconds (avg)",
                    "dataAccuracy": "99.7%",
                    "costEfficiency": "High",
                    "securityIncidents": "None (verified)"
                },
                "complianceCertifications": ["ISO 27001", "GDPR Compliant", "SOC 2"],
                "customerSatisfaction": "4.8/5.0 (based on 825 verified reviews)",
                "verificationMethod": "Independent Service Auditing",
                "attesters": ["TechAudit Alliance", "User Satisfaction Oracle", "Compliance Verification Network"]
            }
        }
    }
    
    # First, check if the identifier exists in our database
    if normalized_identifier not in simulated_reputation_data:
        return {
            "request_data_type": "reputation_score",
            "request_identifier": identifier,
            "source_description": "Decentralized Reputation Network",
            "data_payload": {},
            "verification_summary": "No reputation data found for this identifier.",
            "timestamp": timestamp,
            "error_message": f"No reputation information found for identifier '{identifier}'."
        }
    
    # Check if a specific aspect was requested in query_details
    requested_aspect = None
    if query_details:
        if "aspect=developer" in query_details:
            requested_aspect = "developer"
        elif "aspect=contributor" in query_details:
            requested_aspect = "contributor"
        elif "aspect=service" in query_details:
            requested_aspect = "service"
    
    # Determine which aspect to return based on:
    # 1. Requested aspect (if available for this entity)
    # 2. Entity type's specialized aspect (if available)
    # 3. Default to "general"
    
    available_aspects = simulated_reputation_data[normalized_identifier].keys()
    
    # First try to use the requested aspect if specified and available
    if requested_aspect and requested_aspect in available_aspects:
        reputation_aspect = requested_aspect
    # Next, try to determine the most appropriate specialized aspect
    elif "developer" in available_aspects and "Developer" in normalized_identifier.lower():
        reputation_aspect = "developer"
    elif "service" in available_aspects and "Service" in normalized_identifier.lower():
        reputation_aspect = "service"
    elif "contributor" in available_aspects and "DAO" in normalized_identifier.lower():
        reputation_aspect = "contributor"
    # Special cases based on identifier type
    elif normalized_identifier.startswith("dev") and "developer" in available_aspects:
        reputation_aspect = "developer"
    elif normalized_identifier.startswith("svc") and "service" in available_aspects:
        reputation_aspect = "service"
    # Otherwise fall back to general
    else:
        reputation_aspect = "general"  # Default
    
    # Cache key for reputation data
    cache_key = f"reputation_{normalized_identifier}_{reputation_aspect}"
    
    # Check cache first
    if cache_key in reputation_cache and (datetime.utcnow() - reputation_cache[cache_key]["cached_at"]).total_seconds() < CACHE_EXPIRY_SECONDS:
        reputation_data = reputation_cache[cache_key]["data"]
    else:
        # Get the data for the determined aspect
        reputation_data = simulated_reputation_data[normalized_identifier].get(reputation_aspect)
        
        if reputation_data:
            # Update cache
            reputation_cache[cache_key] = {
                "data": reputation_data,
                "cached_at": datetime.utcnow()
            }
    
    if reputation_data:
        # Format the response with the retrieved reputation data
        return {
            "request_data_type": "reputation_score",
            "request_identifier": identifier,
            "source_description": "Decentralized Reputation Network",
            "data_payload": {
                "entityInfo": {
                    "name": reputation_data["name"],
                    "decentralizedId": reputation_data["did"]
                },
                "reputationScores": {
                    "overall": reputation_data.get("overallScore") or 
                               reputation_data.get("developerScore") or 
                               reputation_data.get("contributorReputation") or 
                               reputation_data.get("serviceScore"),
                    "breakdown": reputation_data.get("reputationBreakdown", {})
                },
                "statistics": reputation_data.get("contributionStats") or 
                              reputation_data.get("codeStats") or 
                              reputation_data.get("governanceStats") or 
                              reputation_data.get("contributionStats") or 
                              reputation_data.get("serviceStats") or
                              reputation_data.get("performanceMetrics", {}),
                "highlights": reputation_data.get("topSkills") or 
                              reputation_data.get("significantProjects") or 
                              reputation_data.get("significantContributions") or
                              reputation_data.get("complianceCertifications", []),
                "verification": {
                    "method": reputation_data["verificationMethod"],
                    "attesters": reputation_data["attesters"],
                    "proofReference": reputation_data.get("activeScoreProof", ""),
                    "timestamp": timestamp
                }
            },
            "verification_summary": f"Reputation data verified through {reputation_data['verificationMethod']} with attestations from {', '.join(reputation_data['attesters'])}.",
            "timestamp": timestamp
        }
    else:
        # If we got here, the entity exists but the aspect doesn't
        available_aspects_list = ", ".join(available_aspects)
        return {
            "request_data_type": "reputation_score",
            "request_identifier": identifier,
            "source_description": "Decentralized Reputation Network",
            "data_payload": {},
            "verification_summary": f"No reputation data found for aspect '{reputation_aspect}'.",
            "timestamp": timestamp,
            "error_message": f"No reputation information found for identifier '{identifier}' with aspect '{reputation_aspect}'. Available aspects: {available_aspects_list}."
        } 