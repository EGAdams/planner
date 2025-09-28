from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json
import logging
from .matching_algorithms import BaseMatcher, ExactMatcher, FuzzyMatcher, CompositeMatcher

logger = logging.getLogger(__name__)

class DuplicateDetector:
    """Main duplicate detection engine for bank transactions"""

    def __init__(self,
                 exact_threshold: float = 1.0,
                 fuzzy_threshold: float = 0.85,
                 use_composite: bool = True):
        """
        Initialize duplicate detector

        Args:
            exact_threshold: Threshold for exact matches (default: 1.0)
            fuzzy_threshold: Threshold for fuzzy matches (default: 0.85)
            use_composite: Whether to use composite matching (default: True)
        """
        self.exact_threshold = exact_threshold
        self.fuzzy_threshold = fuzzy_threshold
        self.use_composite = use_composite

        # Initialize matchers
        self.exact_matcher = ExactMatcher(date_tolerance_days=0)
        self.fuzzy_matcher = FuzzyMatcher(
            date_tolerance_days=2,
            amount_tolerance_percent=0.01,
            description_threshold=0.8
        )

        if use_composite:
            self.composite_matcher = CompositeMatcher([
                (self.exact_matcher, 0.7),
                (self.fuzzy_matcher, 0.3)
            ])

    def find_duplicates(self,
                       new_transactions: List[Dict[str, Any]],
                       existing_transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find potential duplicates between new and existing transactions

        Args:
            new_transactions: List of new transactions to check
            existing_transactions: List of existing transactions in database

        Returns:
            List of duplicate flags with similarity scores and match details
        """
        duplicate_flags = []

        for new_tx in new_transactions:
            duplicates = self._find_duplicates_for_transaction(new_tx, existing_transactions)
            duplicate_flags.extend(duplicates)

        return duplicate_flags

    def _find_duplicates_for_transaction(self,
                                       new_transaction: Dict[str, Any],
                                       existing_transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find duplicates for a single transaction"""
        duplicates = []

        for existing_tx in existing_transactions:
            # Skip if different organizations
            if (new_transaction.get('org_id') != existing_tx.get('org_id')):
                continue

            # Calculate similarity using different matchers
            exact_score = self.exact_matcher.calculate_similarity(new_transaction, existing_tx)
            fuzzy_score = self.fuzzy_matcher.calculate_similarity(new_transaction, existing_tx)

            # Determine if it's a duplicate
            is_duplicate = False
            confidence_score = 0.0
            match_criteria = {}

            if exact_score >= self.exact_threshold:
                is_duplicate = True
                confidence_score = exact_score
                match_criteria = self.exact_matcher.get_match_criteria(new_transaction, existing_tx)
                match_criteria['match_type'] = 'exact'

            elif self.use_composite:
                composite_score = self.composite_matcher.calculate_similarity(new_transaction, existing_tx)
                if composite_score >= self.fuzzy_threshold:
                    is_duplicate = True
                    confidence_score = composite_score
                    match_criteria = self.composite_matcher.get_match_criteria(new_transaction, existing_tx)
                    match_criteria['match_type'] = 'composite'

            elif fuzzy_score >= self.fuzzy_threshold:
                is_duplicate = True
                confidence_score = fuzzy_score
                match_criteria = self.fuzzy_matcher.get_match_criteria(new_transaction, existing_tx)
                match_criteria['match_type'] = 'fuzzy'

            if is_duplicate:
                duplicate_flag = self._create_duplicate_flag(
                    new_transaction,
                    existing_tx,
                    confidence_score,
                    match_criteria
                )
                duplicates.append(duplicate_flag)

        return duplicates

    def _create_duplicate_flag(self,
                             new_transaction: Dict[str, Any],
                             existing_transaction: Dict[str, Any],
                             confidence_score: float,
                             match_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Create a duplicate flag record"""
        return {
            'new_transaction': new_transaction,
            'existing_transaction': existing_transaction,
            'confidence_score': confidence_score,
            'match_criteria': json.dumps(match_criteria),
            'status': 'PENDING',
            'created_at': datetime.now(),
            'duplicate_type': match_criteria.get('match_type', 'unknown')
        }

    def group_duplicates(self, duplicate_flags: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group duplicate flags by transaction

        Args:
            duplicate_flags: List of duplicate flags

        Returns:
            Dictionary mapping transaction identifiers to their duplicate flags
        """
        groups = {}

        for flag in duplicate_flags:
            new_tx = flag['new_transaction']
            tx_key = self._get_transaction_key(new_tx)

            if tx_key not in groups:
                groups[tx_key] = []

            groups[tx_key].append(flag)

        return groups

    def _get_transaction_key(self, transaction: Dict[str, Any]) -> str:
        """Generate a unique key for transaction grouping"""
        date = transaction.get('transaction_date', '')
        amount = transaction.get('amount', 0)
        desc = transaction.get('description', '')[:50]  # First 50 chars

        return f"{date}|{amount}|{desc}"

    def get_high_confidence_duplicates(self,
                                     duplicate_flags: List[Dict[str, Any]],
                                     confidence_threshold: float = 0.95) -> List[Dict[str, Any]]:
        """
        Filter duplicate flags to only high-confidence matches

        Args:
            duplicate_flags: List of duplicate flags
            confidence_threshold: Minimum confidence score

        Returns:
            List of high-confidence duplicate flags
        """
        return [
            flag for flag in duplicate_flags
            if flag['confidence_score'] >= confidence_threshold
        ]

    def generate_duplicate_report(self, duplicate_flags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary report of duplicate detection results

        Args:
            duplicate_flags: List of duplicate flags

        Returns:
            Summary report dictionary
        """
        if not duplicate_flags:
            return {
                'total_duplicates': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'exact_matches': 0,
                'fuzzy_matches': 0,
                'composite_matches': 0
            }

        # Count by confidence levels
        high_confidence = len([f for f in duplicate_flags if f['confidence_score'] >= 0.95])
        medium_confidence = len([f for f in duplicate_flags if 0.8 <= f['confidence_score'] < 0.95])
        low_confidence = len([f for f in duplicate_flags if f['confidence_score'] < 0.8])

        # Count by match types
        exact_matches = len([f for f in duplicate_flags if f['duplicate_type'] == 'exact'])
        fuzzy_matches = len([f for f in duplicate_flags if f['duplicate_type'] == 'fuzzy'])
        composite_matches = len([f for f in duplicate_flags if f['duplicate_type'] == 'composite'])

        return {
            'total_duplicates': len(duplicate_flags),
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'exact_matches': exact_matches,
            'fuzzy_matches': fuzzy_matches,
            'composite_matches': composite_matches,
            'average_confidence': sum(f['confidence_score'] for f in duplicate_flags) / len(duplicate_flags)
        }

class DuplicateDetectionConfig:
    """Configuration class for duplicate detection settings"""

    def __init__(self):
        self.exact_date_tolerance_days = 0
        self.fuzzy_date_tolerance_days = 2
        self.amount_tolerance_percent = 0.01
        self.description_similarity_threshold = 0.8
        self.exact_match_threshold = 1.0
        self.fuzzy_match_threshold = 0.85
        self.composite_match_threshold = 0.85
        self.auto_skip_threshold = 0.98  # Auto-skip duplicates above this threshold

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'DuplicateDetectionConfig':
        """Create config from dictionary"""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }