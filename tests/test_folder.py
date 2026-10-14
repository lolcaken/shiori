"""Tests for shiori.naming.folder — safe on-disk folder names."""
import pytest

from shiori.core.errors import UsageError
from shiori.naming.folder import sanitize_folder_name


def test_plain_display_name_passes_through():
    assert sanitize_folder_name("Some Channel") == "Some Channel"


def test_windows_illegal_characters_are_replaced():
    assert sanitize_folder_name('A:B/C\\D*E?F"G<H>I|J') == "A_B_C_D_E_F_G_H_I_J"


def test_trailing_dots_and_spaces_are_stripped():
    assert sanitize_folder_name("Channel Name. ") == "Channel Name"


def test_leading_and_trailing_whitespace_is_stripped():
    assert sanitize_folder_name("  Some Channel\n") == "Some Channel"


def test_blank_name_is_rejected():
    with pytest.raises(UsageError):
        sanitize_folder_name("   ")
