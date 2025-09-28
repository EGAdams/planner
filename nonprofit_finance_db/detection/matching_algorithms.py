from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
import difflib
from datetime import datetime, timedelta
import json

class BaseMatcher(ABC):
    """Base class for transaction matching algorithms"""

    @abstractmethod
    def calculate_similarity(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> float:
        """
        Calculate similarity score between two transactions

        Args:
            transaction1: First transaction
            transaction2: Second transaction

        Returns:
            Similarity score between 0.0 and 1.0
        """
        pass

    @abstractmethod
    def get_match_criteria(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed match criteria used for comparison

        Args:
            transaction1: First transaction
            transaction2: Second transaction

        Returns:
            Dictionary describing what criteria matched
        """
        pass

class ExactMatcher(BaseMatcher):
    """Exact matching algorithm for identical transactions"""

    def __init__(self, date_tolerance_days: int = 0):
        self.date_tolerance_days = date_tolerance_days

    def calculate_similarity(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> float:
        """Calculate exact match similarity (0.0 or 1.0)"""
        criteria = self.get_match_criteria(transaction1, transaction2)

        # All criteria must match for exact match
        if all(criteria.values()):
            return 1.0
        else:
            return 0.0

    def get_match_criteria(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> Dict[str, Any]:
        """Check exact match criteria"""
        criteria = {}

        # Date matching with tolerance
        criteria['date_match'] = self._dates_match(
            transaction1.get('transaction_date'),
            transaction2.get('transaction_date')
        )

        # Exact amount match
        criteria['amount_match'] = self._amounts_match(
            transaction1.get('amount'),
            transaction2.get('amount')
        )

        # Description exact match (case insensitive)
        criteria['description_match'] = self._descriptions_match(
            transaction1.get('description'),
            transaction2.get('description')
        )

        # Bank reference match if available
        ref1 = transaction1.get('bank_reference')
        ref2 = transaction2.get('bank_reference')
        if ref1 and ref2:
            criteria['reference_match'] = ref1.strip().lower() == ref2.strip().lower()
        else:
            criteria['reference_match'] = True  # Not considered if not available

        return criteria

    def _dates_match(self, date1: str, date2: str) -> bool:
        """Check if dates match within tolerance"""
        if not date1 or not date2:
            return False

        try:
            d1 = datetime.strptime(date1, '%Y-%m-%d')
            d2 = datetime.strptime(date2, '%Y-%m-%d')
            diff = abs((d1 - d2).days)
            return diff <= self.date_tolerance_days
        except ValueError:
            return False

    def _amounts_match(self, amount1: Any, amount2: Any) -> bool:
        """Check if amounts match exactly"""
        try:
            a1 = float(amount1) if amount1 is not None else None
            a2 = float(amount2) if amount2 is not None else None

            if a1 is None or a2 is None:
                return False

            # Use small epsilon for floating point comparison
            return abs(a1 - a2) < 0.001
        except (ValueError, TypeError):
            return False

    def _descriptions_match(self, desc1: str, desc2: str) -> bool:
        """Check if descriptions match exactly (case insensitive)"""
        if not desc1 or not desc2:
            return False

        return desc1.strip().lower() == desc2.strip().lower()

class FuzzyMatcher(BaseMatcher):
    """Fuzzy matching algorithm using string similarity"""

    def __init__(self,
                 date_tolerance_days: int = 2,
                 amount_tolerance_percent: float = 0.01,
                 description_threshold: float = 0.8):
        self.date_tolerance_days = date_tolerance_days
        self.amount_tolerance_percent = amount_tolerance_percent
        self.description_threshold = description_threshold

    def calculate_similarity(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> float:
        """Calculate fuzzy similarity score"""
        scores = []
        weights = []

        # Date similarity (weight: 0.3)
        date_score = self._calculate_date_similarity(
            transaction1.get('transaction_date'),
            transaction2.get('transaction_date')
        )
        scores.append(date_score)
        weights.append(0.3)

        # Amount similarity (weight: 0.4)
        amount_score = self._calculate_amount_similarity(
            transaction1.get('amount'),
            transaction2.get('amount')
        )
        scores.append(amount_score)
        weights.append(0.4)

        # Description similarity (weight: 0.3)
        desc_score = self._calculate_description_similarity(
            transaction1.get('description'),
            transaction2.get('description')
        )
        scores.append(desc_score)
        weights.append(0.3)

        # Calculate weighted average
        total_weight = sum(weights)
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_match_criteria(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed fuzzy match criteria"""
        return {
            'date_similarity': self._calculate_date_similarity(
                transaction1.get('transaction_date'),
                transaction2.get('transaction_date')
            ),
            'amount_similarity': self._calculate_amount_similarity(
                transaction1.get('amount'),
                transaction2.get('amount')
            ),
            'description_similarity': self._calculate_description_similarity(
                transaction1.get('description'),
                transaction2.get('description')
            ),
            'overall_similarity': self.calculate_similarity(transaction1, transaction2)
        }

    def _calculate_date_similarity(self, date1: str, date2: str) -> float:
        """Calculate date similarity based on tolerance"""
        if not date1 or not date2:
            return 0.0

        try:
            d1 = datetime.strptime(date1, '%Y-%m-%d')
            d2 = datetime.strptime(date2, '%Y-%m-%d')
            diff_days = abs((d1 - d2).days)

            if diff_days == 0:
                return 1.0
            elif diff_days <= self.date_tolerance_days:
                return 1.0 - (diff_days / self.date_tolerance_days) * 0.5
            else:
                return 0.0
        except ValueError:
            return 0.0

    def _calculate_amount_similarity(self, amount1: Any, amount2: Any) -> float:
        """Calculate amount similarity based on tolerance"""
        try:
            a1 = float(amount1) if amount1 is not None else None
            a2 = float(amount2) if amount2 is not None else None

            if a1 is None or a2 is None:
                return 0.0

            if abs(a1 - a2) < 0.001:  # Exact match
                return 1.0

            # Calculate percentage difference
            avg_amount = (abs(a1) + abs(a2)) / 2
            if avg_amount == 0:
                return 1.0 if a1 == a2 else 0.0

            diff_percent = abs(a1 - a2) / avg_amount

            if diff_percent <= self.amount_tolerance_percent:
                return 1.0 - (diff_percent / self.amount_tolerance_percent) * 0.3
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0

    def _calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate description similarity using sequence matcher"""
        if not desc1 or not desc2:
            return 0.0

        # Normalize descriptions
        d1 = self._normalize_description(desc1)
        d2 = self._normalize_description(desc2)

        # Use SequenceMatcher for similarity
        matcher = difflib.SequenceMatcher(None, d1, d2)
        return matcher.ratio()

    def _normalize_description(self, description: str) -> str:
        """Normalize description for comparison"""
        if not description:
            return ''

        # Convert to lowercase and remove extra whitespace
        normalized = ' '.join(description.lower().strip().split())

        # Remove common transaction codes and formatting
        normalized = normalized.replace('**', '').replace('***', '')
        normalized = normalized.replace('#', '').replace('*', '')

        return normalized

class CompositeMatcher(BaseMatcher):
    """Composite matcher that combines multiple matching algorithms"""

    def __init__(self, matchers: List[Tuple[BaseMatcher, float]]):
        """
        Initialize composite matcher

        Args:
            matchers: List of (matcher, weight) tuples
        """
        self.matchers = matchers
        self.total_weight = sum(weight for _, weight in matchers)

    def calculate_similarity(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> float:
        """Calculate composite similarity score"""
        if not self.matchers or self.total_weight == 0:
            return 0.0

        weighted_sum = 0.0
        for matcher, weight in self.matchers:
            score = matcher.calculate_similarity(transaction1, transaction2)
            weighted_sum += score * weight

        return weighted_sum / self.total_weight

    def get_match_criteria(self, transaction1: Dict[str, Any], transaction2: Dict[str, Any]) -> Dict[str, Any]:
        """Get combined match criteria from all matchers"""
        combined_criteria = {}

        for i, (matcher, weight) in enumerate(self.matchers):
            criteria = matcher.get_match_criteria(transaction1, transaction2)
            matcher_name = matcher.__class__.__name__

            combined_criteria[f'{matcher_name}_criteria'] = criteria
            combined_criteria[f'{matcher_name}_weight'] = weight
            combined_criteria[f'{matcher_name}_score'] = matcher.calculate_similarity(transaction1, transaction2)

        combined_criteria['composite_score'] = self.calculate_similarity(transaction1, transaction2)

        return combined_criteria