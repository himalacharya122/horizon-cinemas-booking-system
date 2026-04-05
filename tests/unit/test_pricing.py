"""
tests/unit/test_pricing.py
──────────────────────────
Unit tests for the BasePrice pricing model.

Price rules from spec:
  - Upper gallery = lower_hall_price * 1.20
  - VIP           = lower_hall_price * 1.20 * 1.20  (= *1.44)

Test cases:
  TC-PRC-01  Lower hall price returned directly
  TC-PRC-02  Upper gallery = lower * 1.20
  TC-PRC-03  VIP = lower * 1.44  (spec example: £10 → £14.40)
  TC-PRC-04  Bristol evening prices (£8 lower, £9.60 upper, £11.52 VIP)
  TC-PRC-05  London morning prices (£10, £12, £14.40)
  TC-PRC-06  Birmingham morning (£5 → £6.00 upper → £7.20 VIP)
  TC-PRC-07  Invalid seat type raises ValueError
  TC-PRC-08  Prices round to 2 decimal places
"""

import pytest # type: ignore
from decimal import Decimal

from backend.models.booking import BasePrice


class TestPricing:

    def _make_bp(self, price: float) -> BasePrice:
        bp = BasePrice.__new__(BasePrice)
        bp.lower_hall_price = Decimal(str(price))
        bp.city_id = 1
        bp.show_period = "evening"
        return bp

    def test_lower_hall_returned_directly(self):
        """TC-PRC-01"""
        bp = self._make_bp(8.00)
        assert bp.price_for_seat_type("lower_hall") == 8.00

    def test_upper_gallery_is_lower_times_1_20(self):
        """TC-PRC-02"""
        bp = self._make_bp(10.00)
        assert bp.upper_gallery_price == 12.00
        assert bp.price_for_seat_type("upper_gallery") == 12.00

    def test_vip_spec_example_10_becomes_14_40(self):
        """TC-PRC-03: Spec example — £10 lower → VIP = £14.40."""
        bp = self._make_bp(10.00)
        assert bp.vip_price == 14.40
        assert bp.price_for_seat_type("vip") == 14.40

    def test_bristol_evening_prices(self):
        """TC-PRC-04: Bristol evening = £8 lower, £9.60 upper, £11.52 VIP."""
        bp = self._make_bp(8.00)
        assert bp.price_for_seat_type("lower_hall") == 8.00
        assert bp.price_for_seat_type("upper_gallery") == 9.60
        assert bp.price_for_seat_type("vip") == 11.52

    def test_london_morning_prices(self):
        """TC-PRC-05: London morning = £10 lower, £12 upper, £14.40 VIP."""
        bp = self._make_bp(10.00)
        assert bp.price_for_seat_type("lower_hall") == 10.00
        assert bp.price_for_seat_type("upper_gallery") == 12.00
        assert bp.price_for_seat_type("vip") == 14.40

    def test_birmingham_morning_prices(self):
        """TC-PRC-06: Birmingham morning = £5 lower, £6.00 upper, £7.20 VIP."""
        bp = self._make_bp(5.00)
        assert bp.price_for_seat_type("lower_hall") == 5.00
        assert bp.price_for_seat_type("upper_gallery") == 6.00
        assert bp.price_for_seat_type("vip") == 7.20

    def test_invalid_seat_type_raises(self):
        """TC-PRC-07"""
        bp = self._make_bp(10.00)
        with pytest.raises(ValueError, match="Unknown seat type"):
            bp.price_for_seat_type("premium_deluxe")

    def test_prices_round_to_2_decimals(self):
        """TC-PRC-08: Odd base price still rounds correctly."""
        bp = self._make_bp(7.00)
        # upper = 7 * 1.20 = 8.40
        assert bp.upper_gallery_price == 8.40
        # vip = 7 * 1.44 = 10.08
        assert bp.vip_price == 10.08

    def test_all_city_prices_from_spec(self):
        """Verify all prices from the spec table."""
        spec = {
            "Birmingham": {"morning": 5, "afternoon": 6, "evening": 7},
            "Bristol":    {"morning": 6, "afternoon": 7, "evening": 8},
            "Cardiff":    {"morning": 5, "afternoon": 6, "evening": 7},
            "London":     {"morning": 10, "afternoon": 11, "evening": 12},
        }
        for city, periods in spec.items():
            for period, lower in periods.items():
                bp = self._make_bp(lower)
                expected_upper = round(lower * 1.20, 2)
                expected_vip = round(lower * 1.44, 2)
                assert bp.price_for_seat_type("lower_hall") == lower, \
                    f"{city} {period} lower_hall"
                assert bp.price_for_seat_type("upper_gallery") == expected_upper, \
                    f"{city} {period} upper_gallery"
                assert bp.price_for_seat_type("vip") == expected_vip, \
                    f"{city} {period} vip"