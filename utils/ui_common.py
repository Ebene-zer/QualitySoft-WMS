from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

# Shared UI constants
DEFAULT_BUTTON_MIN_WIDTH = 300
DEFAULT_SEARCH_WIDTH = 300
DEFAULT_DEBOUNCE_MS = 250

SEARCH_PLACEHOLDER_PRODUCTS = "Search products by ID, name, price, or stock…"
SEARCH_TOOLTIP_PRODUCTS = "Type to filter products by any field (ID, name, price, stock)"

SEARCH_PLACEHOLDER_CUSTOMERS = "Search customers by ID, name, phone, or address…"
SEARCH_TOOLTIP_CUSTOMERS = "Type to filter customers by any field (ID, name, phone, address)"


def format_money(amount) -> str:
    """Format a value as Ghana cedi currency with two decimals, including symbol.

    Examples:
        1234.5 -> "GH¢ 1,234.50"
        "1234.5" -> "GH¢ 1,234.50"
        None -> "GH¢ 0.00"
    """
    try:
        # Accept strings like "GH¢ 1,234.56"
        if isinstance(amount, str):
            cleaned = amount.replace("GH¢", "").replace(",", "").strip()
            value = float(cleaned)
        else:
            value = float(amount)
    except Exception:
        value = 0.0
    return f"GH¢ {value:,.2f}"


def format_money_value(amount) -> str:
    """Format a numeric amount with two decimals and thousands separators, without currency symbol.

    Accepts strings that might include "GH¢" or commas and normalizes to a plain number string.
    Examples:
        1234.5 -> "1,234.50"
        "GH¢ 1,234.5" -> "1,234.50"
        None -> "0.00"
    """
    try:
        if isinstance(amount, str):
            cleaned = amount.replace("GH¢", "").replace(",", "").strip()
            value = float(cleaned or 0)
        else:
            value = float(amount)
    except Exception:
        value = 0.0
    return f"{value:,.2f}"


def create_top_actions_row(
    parent,
    button_text: str,
    button_handler,
    search_placeholder: str,
    search_tooltip: str,
    on_search_timeout,
    *,
    button_min_width: int = DEFAULT_BUTTON_MIN_WIDTH,
    search_fixed_width: int = DEFAULT_SEARCH_WIDTH,
    debounce_ms: int = DEFAULT_DEBOUNCE_MS,
):
    """Create a reusable top actions row with a left-aligned button and right-aligned search.

    Returns (layout, search_input, search_timer, add_button).
    """
    add_button = QPushButton(button_text, parent)
    if button_min_width:
        add_button.setMinimumWidth(button_min_width)
    add_button.clicked.connect(button_handler)

    search_input = QLineEdit(parent)
    if search_placeholder:
        search_input.setPlaceholderText(search_placeholder)
    search_input.setClearButtonEnabled(True)
    if search_tooltip:
        search_input.setToolTip(search_tooltip)
    if search_fixed_width:
        search_input.setFixedWidth(search_fixed_width)

    # Debounce search to avoid filtering on every keystroke
    timer = QTimer(parent)
    timer.setSingleShot(True)
    timer.setInterval(debounce_ms)
    timer.timeout.connect(on_search_timeout)

    def _on_text_changed(_text: str):
        if timer.isActive():
            timer.stop()
        timer.start()

    search_input.textChanged.connect(_on_text_changed)

    layout = QHBoxLayout()
    layout.addWidget(add_button)
    layout.addStretch(1)
    layout.addWidget(search_input)
    return layout, search_input, timer, add_button
