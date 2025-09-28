"""
Tests for duplicate detection system
"""

import pytest
from unittest.mock import Mock
from detection.matching_algorithms import ExactMatcher, FuzzyMatcher, CompositeMatcher
from detection.duplicate_detector import DuplicateDetector


class TestExactMatcher:
    """Test exact matching algorithm"""

    def test_exact_match_identical_transactions(self):
        """Test exact match for identical transactions"""
        matcher = ExactMatcher(date_tolerance_days=0)

        tx1 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test Transaction',
            'bank_reference': 'REF001'
        }

        tx2 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test Transaction',
            'bank_reference': 'REF001'
        }

        similarity = matcher.calculate_similarity(tx1, tx2)
        assert similarity == 1.0

        criteria = matcher.get_match_criteria(tx1, tx2)
        assert criteria['date_match'] == True
        assert criteria['amount_match'] == True
        assert criteria['description_match'] == True
        assert criteria['reference_match'] == True

    def test_exact_match_different_transactions(self):
        """Test exact match for different transactions"""
        matcher = ExactMatcher(date_tolerance_days=0)

        tx1 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test Transaction',
        }

        tx2 = {
            'transaction_date': '2024-01-02',
            'amount': 200.00,
            'description': 'Different Transaction',
        }

        similarity = matcher.calculate_similarity(tx1, tx2)
        assert similarity == 0.0

    def test_date_tolerance(self):
        """Test date tolerance functionality"""
        matcher = ExactMatcher(date_tolerance_days=1)

        tx1 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test Transaction',
        }

        tx2 = {
            'transaction_date': '2024-01-02',  # 1 day difference
            'amount': 100.00,
            'description': 'Test Transaction',
        }

        criteria = matcher.get_match_criteria(tx1, tx2)
        assert criteria['date_match'] == True  # Within tolerance

        tx3 = {
            'transaction_date': '2024-01-03',  # 2 days difference
            'amount': 100.00,
            'description': 'Test Transaction',
        }

        criteria = matcher.get_match_criteria(tx1, tx3)
        assert criteria['date_match'] == False  # Outside tolerance

    def test_case_insensitive_description(self):
        """Test case insensitive description matching"""
        matcher = ExactMatcher()

        tx1 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test Transaction',
        }

        tx2 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'TEST TRANSACTION',
        }

        criteria = matcher.get_match_criteria(tx1, tx2)
        assert criteria['description_match'] == True


class TestFuzzyMatcher:
    """Test fuzzy matching algorithm"""

    def test_fuzzy_match_similar_transactions(self):
        """Test fuzzy matching for similar transactions"""
        matcher = FuzzyMatcher()

        tx1 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Amazon Marketplace Purchase',
        }

        tx2 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'AMZN MKTP Purchase',
        }

        similarity = matcher.calculate_similarity(tx1, tx2)
        assert similarity > 0.5  # Should be somewhat similar

    def test_date_similarity(self):
        """Test date similarity calculation"""
        matcher = FuzzyMatcher(date_tolerance_days=2)

        # Same date
        similarity = matcher._calculate_date_similarity('2024-01-01', '2024-01-01')
        assert similarity == 1.0

        # One day difference
        similarity = matcher._calculate_date_similarity('2024-01-01', '2024-01-02')
        assert similarity > 0.5

        # Beyond tolerance
        similarity = matcher._calculate_date_similarity('2024-01-01', '2024-01-05')
        assert similarity == 0.0

    def test_amount_similarity(self):
        """Test amount similarity calculation"""
        matcher = FuzzyMatcher(amount_tolerance_percent=0.01)

        # Exact match
        similarity = matcher._calculate_amount_similarity(100.00, 100.00)
        assert similarity == 1.0

        # Small difference within tolerance
        similarity = matcher._calculate_amount_similarity(100.00, 100.50)
        assert similarity > 0.7

        # Large difference
        similarity = matcher._calculate_amount_similarity(100.00, 200.00)
        assert similarity == 0.0

    def test_description_similarity(self):
        """Test description similarity calculation"""
        matcher = FuzzyMatcher()

        # Identical descriptions
        similarity = matcher._calculate_description_similarity('Test Transaction', 'Test Transaction')
        assert similarity == 1.0

        # Similar descriptions
        similarity = matcher._calculate_description_similarity('Amazon Purchase', 'AMZN Purchase')
        assert similarity > 0.5

        # Different descriptions
        similarity = matcher._calculate_description_similarity('Amazon Purchase', 'Starbucks Coffee')
        assert similarity < 0.3

    def test_normalize_description(self):
        """Test description normalization"""
        matcher = FuzzyMatcher()

        # Test normalization
        normalized = matcher._normalize_description('  **AMAZON** MARKETPLACE  ')
        assert normalized == 'amazon marketplace'

        normalized = matcher._normalize_description('TEST###TRANSACTION***')
        assert normalized == 'testtransaction'


class TestCompositeMatcher:
    """Test composite matching algorithm"""

    def test_composite_matching(self):
        """Test composite matcher with multiple algorithms"""
        exact_matcher = ExactMatcher()
        fuzzy_matcher = FuzzyMatcher()

        composite_matcher = CompositeMatcher([
            (exact_matcher, 0.7),
            (fuzzy_matcher, 0.3)
        ])

        tx1 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test Transaction',
        }

        tx2 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test Transaction',
        }

        # Exact match should give high score
        similarity = composite_matcher.calculate_similarity(tx1, tx2)
        assert similarity > 0.8

    def test_composite_criteria(self):
        """Test composite match criteria"""
        exact_matcher = ExactMatcher()
        fuzzy_matcher = FuzzyMatcher()

        composite_matcher = CompositeMatcher([
            (exact_matcher, 0.6),
            (fuzzy_matcher, 0.4)
        ])

        tx1 = {'transaction_date': '2024-01-01', 'amount': 100.00, 'description': 'Test'}
        tx2 = {'transaction_date': '2024-01-01', 'amount': 100.00, 'description': 'Test'}

        criteria = composite_matcher.get_match_criteria(tx1, tx2)

        assert 'ExactMatcher_criteria' in criteria
        assert 'FuzzyMatcher_criteria' in criteria
        assert 'ExactMatcher_weight' in criteria
        assert 'FuzzyMatcher_weight' in criteria
        assert 'composite_score' in criteria


class TestDuplicateDetector:
    """Test main duplicate detector"""

    def test_find_duplicates_basic(self):
        """Test basic duplicate detection"""
        detector = DuplicateDetector()

        new_transactions = [
            {
                'org_id': 1,
                'transaction_date': '2024-01-01',
                'amount': 100.00,
                'description': 'Test Transaction',
            }
        ]

        existing_transactions = [
            {
                'org_id': 1,
                'transaction_date': '2024-01-01',
                'amount': 100.00,
                'description': 'Test Transaction',
            }
        ]

        duplicates = detector.find_duplicates(new_transactions, existing_transactions)

        assert len(duplicates) == 1
        assert duplicates[0]['confidence_score'] == 1.0

    def test_find_duplicates_different_orgs(self):
        """Test that different organizations don't match"""
        detector = DuplicateDetector()

        new_transactions = [
            {
                'org_id': 1,
                'transaction_date': '2024-01-01',
                'amount': 100.00,
                'description': 'Test Transaction',
            }
        ]

        existing_transactions = [
            {
                'org_id': 2,  # Different org
                'transaction_date': '2024-01-01',
                'amount': 100.00,
                'description': 'Test Transaction',
            }
        ]

        duplicates = detector.find_duplicates(new_transactions, existing_transactions)
        assert len(duplicates) == 0

    def test_high_confidence_duplicates(self):
        """Test filtering high confidence duplicates"""
        detector = DuplicateDetector()

        duplicate_flags = [
            {'confidence_score': 1.0, 'status': 'PENDING'},
            {'confidence_score': 0.9, 'status': 'PENDING'},
            {'confidence_score': 0.8, 'status': 'PENDING'},
        ]

        high_confidence = detector.get_high_confidence_duplicates(duplicate_flags, 0.95)
        assert len(high_confidence) == 1
        assert high_confidence[0]['confidence_score'] == 1.0

    def test_group_duplicates(self):
        """Test grouping duplicates by transaction"""
        detector = DuplicateDetector()

        duplicate_flags = [
            {
                'new_transaction': {
                    'transaction_date': '2024-01-01',
                    'amount': 100.00,
                    'description': 'Test Transaction'
                },
                'confidence_score': 1.0
            },
            {
                'new_transaction': {
                    'transaction_date': '2024-01-01',
                    'amount': 100.00,
                    'description': 'Test Transaction'
                },
                'confidence_score': 0.9
            }
        ]

        groups = detector.group_duplicates(duplicate_flags)
        assert len(groups) == 1  # Should group together

    def test_duplicate_report(self):
        """Test duplicate detection report generation"""
        detector = DuplicateDetector()

        duplicate_flags = [
            {'confidence_score': 1.0, 'duplicate_type': 'exact'},
            {'confidence_score': 0.9, 'duplicate_type': 'fuzzy'},
            {'confidence_score': 0.8, 'duplicate_type': 'composite'},
        ]

        report = detector.generate_duplicate_report(duplicate_flags)

        assert report['total_duplicates'] == 3
        assert report['high_confidence'] == 1
        assert report['medium_confidence'] == 2
        assert report['low_confidence'] == 0
        assert report['exact_matches'] == 1
        assert report['fuzzy_matches'] == 1
        assert report['composite_matches'] == 1
        assert 'average_confidence' in report

    def test_empty_duplicate_report(self):
        """Test report generation with no duplicates"""
        detector = DuplicateDetector()

        report = detector.generate_duplicate_report([])

        assert report['total_duplicates'] == 0
        assert report['high_confidence'] == 0
        assert report['exact_matches'] == 0


if __name__ == '__main__':
    pytest.main([__file__])