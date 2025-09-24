import logging
import os
import sys
from datetime import datetime

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from ui.about_dialog import AboutDialog
from ui.customer_view import CustomerView
from ui.help_dialog import HelpDialog
from ui.invoice_view import InvoiceView
from ui.more import MoreDropdown
from ui.product_view import ProductView
from ui.receipt_view import ReceiptView
from ui.settings_dialog import SettingsDialog

# Ensure UserView is available as an attribute on this module for tests that patch ui.main_window.UserView
from ui.user_view import UserView  # noqa: F401
from ui.users_dialog import UsersDialog
from utils.backup import needs_backup, perform_backup
from utils.branding import APP_NAME
from utils.session import get_current_username, get_welcome_shown, set_welcome_shown


class MainWindow(QWidget):
    def __init__(self, logged_in_user, role):
        super().__init__()
        self.logged_in_user = logged_in_user
        self.user_role = role
        self.setWindowTitle(APP_NAME)
        self.resize(1000, 700)
        self.setMinimumSize(600, 400)

        # Scrolling tagline in title bar
        try:
            enable_marquee = ("pytest" not in sys.modules) and (os.environ.get("QT_QPA_PLATFORM") != "offscreen")
            if enable_marquee:
                self._title_base = APP_NAME
                self._tagline = "Control Your Wholesale Flow."
                self._marquee_pos = 0
                self._marquee_timer = QTimer(self)
                self._marquee_timer.timeout.connect(self._tick_title_marquee)
                self._marquee_timer.start(500)  # update every 500 ms (slower)
                self._tick_title_marquee()
        except Exception:
            pass

        # Set flat background color
        self.setStyleSheet("background-color: #f0f2f5;")

        main_layout = QVBoxLayout()

        # Menu bar
        menubar = QMenuBar(self)
        # Add Settings to menu bar for Admin/CEO
        if self.user_role.lower() in ["admin", "ceo"]:
            settings_action = menubar.addAction("Settings")
            settings_action.triggered.connect(self.open_settings_dialog)
            # Add Users to menu bar, opens Users dialog window
            users_action = menubar.addAction("Users")
            users_action.triggered.connect(self.open_users_dialog)
        help_action = menubar.addAction("Help")
        help_action.triggered.connect(self.open_help_dialog)
        main_layout.setMenuBar(menubar)

        # Top button bar layout
        button_bar_layout = QHBoxLayout()
        button_bar_layout.setSpacing(12)

        self.nav_buttons = []

        def create_nav_button(text, index, height=40, font_size=10, width=None):
            btn = QPushButton(text)
            btn.setFixedHeight(height)
            btn.setFont(QFont("Segue UI", font_size, QFont.Weight.Medium))
            if width:
                btn.setFixedWidth(width)
            btn.setStyleSheet(self.button_style(normal=True))
            btn.clicked.connect(lambda: self.switch_view(index))
            button_bar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            return btn

        # Place 'More' button first, as a square with tooltip
        btn_more = QPushButton("\u2630")
        btn_more.setFixedHeight(40)
        btn_more.setFixedWidth(40)
        btn_more.setFont(QFont("Segue UI", 14, QFont.Weight.Medium))
        btn_more.setStyleSheet(self.button_style(normal=True))
        btn_more.setToolTip("More")
        btn_more.clicked.connect(lambda: self.switch_view(0))
        button_bar_layout.addWidget(btn_more)
        self.nav_buttons.append(btn_more)

        # Simple Products button (with optional low-stock count badge)
        self.btn_products = create_nav_button("Products", 1, 40, 11)
        # Create badge overlay for Products button
        self._ensure_products_badge()
        self.btn_products.installEventFilter(self)
        create_nav_button("Customers", 2, 40, 11)
        create_nav_button("Invoice", 3, 40, 11)
        create_nav_button("Receipts", 4, 40, 11)

        # Admin/CEO extra navigation buttons removed: Users and Settings are menu-only now

        # Move Logout to the end so it's the last (rightmost) button
        btn_logout = QPushButton("Logout")
        btn_logout.setFixedHeight(40)
        btn_logout.setFont(QFont("Segue UI", 11, QFont.Weight.Medium))
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: orange;
                color: white;
                border-radius: 6px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_logout.clicked.connect(self.logout)
        button_bar_layout.addWidget(btn_logout)

        main_layout.addLayout(button_bar_layout)

        # Central stacked widget
        self.stacked_widget = QStackedWidget()
        # Add More tab first
        more_tab = QWidget()
        more_layout = QVBoxLayout()
        self.more_dropdown_widget = MoreDropdown(user_role=self.user_role)
        more_layout.addWidget(self.more_dropdown_widget)
        more_tab.setLayout(more_layout)
        self.stacked_widget.addWidget(more_tab)

        # Create views
        self.product_view = ProductView(on_low_stock_status_changed=self.update_products_badge)
        self.customer_view = CustomerView()
        self.invoice_view = InvoiceView()
        self.receipt_view = ReceiptView()
        # Users is dialog-only now; no user_view tab
        # self.user_view = UserView(current_user_role=self.user_role)
        self.stacked_widget.addWidget(self.product_view)
        self.stacked_widget.addWidget(self.customer_view)
        self.stacked_widget.addWidget(self.invoice_view)
        self.stacked_widget.addWidget(self.receipt_view)
        # self.stacked_widget.addWidget(self.user_view)
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        # Removed unused refresh_more_features_dialog wiring
        # self.invoice_view.invoice_created.connect(self.refresh_more_features_dialog)
        # self.more_features_dialog = None

        # Set the first button as active
        self.switch_view(3)

        # Show welcome dropdown once per session shortly after window shows
        QTimer.singleShot(200, self.maybe_show_welcome_dropdown)

    def button_style(self, normal=True):
        if normal:
            return """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border-radius: 6px;
                    padding: 8px 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border-radius: 6px;
                    padding: 8px 14px;
                }
            """

    def maybe_show_welcome_dropdown(self):
        try:
            if get_welcome_shown():
                return
            username = get_current_username() or self.logged_in_user or "User"
            hour = datetime.now().hour
            if hour < 12:
                greeting = "Good Morning"
            elif hour < 17:
                greeting = "Good Afternoon"
            elif hour < 21:
                greeting = "Good Evening"
            else:
                greeting = "Good Night"

            # Welcome dropdown using default app colors for maximum readability
            menu = QMenu(self)
            menu.setStyleSheet(
                """
                QMenu {
                    background: #ffffff;
                    color: #2c3e50; /* default dark text */
                    border: 1px solid #3498db; /* app primary */
                    border-radius: 10px;
                    padding: 6px;
                }
                QMenu::item {
                    padding: 10px 14px;
                    background-color: transparent;
                    border-radius: 6px;
                    color: #2c3e50;
                }
                QMenu::item:selected {
                    background-color: #eaf2fb; /* light blue hover */
                }
                QMenu::separator {
                    height: 8px;
                    margin: 6px 10px;
                    background: transparent;
                }
                """
            )

            content = QWidget(self)
            v = QVBoxLayout(content)
            v.setContentsMargins(16, 14, 16, 10)
            v.setSpacing(4)

            title = QLabel(f"{greeting}, {username}!")
            title.setStyleSheet("color: #2c3e50; font-size: 20px; font-weight: 800;")
            subtitle = QLabel(f"Welcome back to {APP_NAME}.")
            subtitle.setStyleSheet("color: #34495e; font-size: 13px; font-weight: 600;")
            tip = QLabel("Have a productive session.")
            tip.setStyleSheet("color: #5d6d7e; font-size: 12px;")

            v.addWidget(title)
            v.addWidget(subtitle)
            v.addWidget(tip)

            wa = QWidgetAction(self)
            wa.setDefaultWidget(content)
            menu.addAction(wa)
            menu.addSeparator()
            dismiss_action = menu.addAction("Dismiss")
            dismiss_action.triggered.connect(lambda: self._fade_slide_close(menu, 650, -28))

            # Width and position from the top center
            menu_width = max(360, menu.sizeHint().width())
            menu.setFixedWidth(menu_width)
            top_left = self.mapToGlobal(self.rect().topLeft())
            target_x = top_left.x() + max(20, (self.width() - menu_width) // 2)
            target_y = top_left.y() + 56  # just below the top bar
            # Start slightly above the target for a noticeable drop
            start_pos = QPoint(target_x, target_y - 28)
            end_pos = QPoint(target_x, target_y)

            # Show menu at start position and animate slide+fade in
            menu.popup(start_pos)
            self._slide_fade_in(menu, end_pos, 700)

            # Keep a reference to avoid garbage collection
            self._welcome_menu = menu
            set_welcome_shown(True)

            # Auto-dismiss after 4 seconds with fade and slide up
            QTimer.singleShot(4000, lambda: self._fade_slide_close(menu, 700, -28))
        except Exception:
            pass

    def _slide_fade_in(self, widget: QWidget, target_pos: QPoint, duration_ms: int = 700):
        """Animate the widget appearing by sliding down to target_pos while fading in."""
        try:
            if widget is None:
                return
            # Opacity effect
            effect = getattr(widget, "_fade_effect", None)
            if effect is None:
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)
                widget._fade_effect = effect
            effect.setOpacity(0.0)

            # Opacity animation 0 -> 1
            fade_anim = QPropertyAnimation(effect, b"opacity", widget)
            fade_anim.setDuration(duration_ms)
            fade_anim.setStartValue(0.0)
            fade_anim.setEndValue(1.0)
            fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            # Position animation: current -> target_pos
            pos_anim = QPropertyAnimation(widget, b"pos", widget)
            pos_anim.setDuration(duration_ms)
            pos_anim.setStartValue(widget.pos())
            pos_anim.setEndValue(target_pos)
            pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            group = QParallelAnimationGroup(widget)
            group.addAnimation(fade_anim)
            group.addAnimation(pos_anim)

            # Keep a ref to prevent GC and start
            widget._show_group = group
            group.start()
        except Exception:
            pass

    def _fade_slide_close(self, widget: QWidget, duration_ms: int = 650, delta_y: int = -24):
        """Animate the widget disappearing by sliding up (delta_y negative) while fading out, then close."""
        try:
            if widget is None:
                return
            # Opacity effect
            effect = getattr(widget, "_fade_effect", None)
            if effect is None:
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)
                widget._fade_effect = effect
            effect.setOpacity(1.0)

            # Opacity animation 1 -> 0
            fade_anim = QPropertyAnimation(effect, b"opacity", widget)
            fade_anim.setDuration(duration_ms)
            fade_anim.setStartValue(1.0)
            fade_anim.setEndValue(0.0)
            fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)

            # Position animation: current -> current + (0, delta_y)
            end_pos = QPoint(widget.pos().x(), widget.pos().y() + delta_y)
            pos_anim = QPropertyAnimation(widget, b"pos", widget)
            pos_anim.setDuration(duration_ms)
            pos_anim.setStartValue(widget.pos())
            pos_anim.setEndValue(end_pos)
            pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)

            group = QParallelAnimationGroup(widget)
            group.addAnimation(fade_anim)
            group.addAnimation(pos_anim)

            def _on_finished():
                try:
                    widget.close()
                finally:
                    try:
                        widget.setGraphicsEffect(None)
                    except Exception:
                        pass

            group.finished.connect(_on_finished)
            # Keep a ref to prevent GC and start
            widget._hide_group = group
            group.start()
        except Exception:
            try:
                widget.close()
            except Exception:
                pass

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)

        # Refresh relevant view when switched to
        widget = self.stacked_widget.currentWidget()
        if hasattr(widget, "load_customers"):
            widget.load_customers()
        if hasattr(widget, "load_products"):
            widget.load_products()
        if hasattr(widget, "load_invoice_ids"):
            widget.load_invoice_ids()
        if hasattr(widget, "load_invoices"):
            widget.load_invoices()
        if hasattr(widget, "load_users"):
            widget.load_users()

        # Update button styles to highlight active one
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet(self.button_style(normal=False))
            else:
                btn.setStyleSheet(self.button_style(normal=True))

    def logout(self):
        from ui.login_window import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def open_about_dialog(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def open_help_dialog(self):
        dlg = HelpDialog(on_about_clicked=self.open_about_dialog, parent=self)
        dlg.exec()

    def open_users_dialog(self):
        dlg = UsersDialog(current_user_role=self.user_role, parent=self)
        dlg.exec()

    def closeEvent(self, event):
        """Perform an automatic backup if one is due before closing. Show UI warning if it fails."""
        try:
            # Stop the marquee timer on close
            try:
                if hasattr(self, "_marquee_timer") and self._marquee_timer is not None:
                    self._marquee_timer.stop()
            except Exception:
                pass

            if needs_backup(hours=24):
                log = logging.getLogger(__name__)
                log.info("Auto backup triggered on exit.")
                try:
                    path = perform_backup()
                    log.info("Auto backup created at %s", path)
                except Exception as e:
                    log.warning("Auto backup failed: %s", e)
                    try:
                        QMessageBox.warning(self, "Backup Failed", f"Automatic backup failed.\n{e}")
                    except Exception:
                        pass
        finally:
            super().closeEvent(event)

    def update_products_badge(self, count: int | None):
        """Update Products button with a dark-red badge showing the low-stock count.
        Uses an overlay QLabel for reliable rendering across styles. Tooltip lists exact products and stock.
        """
        try:
            if not hasattr(self, "btn_products") or self.btn_products is None:
                return
            # Always keep base text plain
            self.btn_products.setText("Products")
            self._ensure_products_badge()
            if isinstance(count, int) and count > 0:
                self._products_badge.setText(str(count))
                self._products_badge.raise_()
                self._products_badge.show()
                self._position_products_badge()
                # Build tooltip with exact products and their stock
                try:
                    from models.product import Product
                    from utils.app_settings import get_low_stock_threshold

                    threshold = get_low_stock_threshold()
                    low_stock = Product.get_products_below_stock(threshold) or []
                    if low_stock:
                        # Limit extremely long tooltips by slicing, but show all if small
                        items_html = "".join(
                            f"<li>{p.name}: <b>{p.stock_quantity}</b> in stock</li>" for p in low_stock
                        )
                        tooltip = f"<b>Low stock products:</b><ul style='margin:4px 0 0 16px;'>{items_html}</ul>"
                    else:
                        tooltip = "Products with low stock present"
                except Exception:
                    tooltip = "Products with low stock present"
                self.btn_products.setToolTip(tooltip)
            else:
                self._products_badge.hide()
                self.btn_products.setToolTip("Products")
        except Exception:
            pass

    # Badge helpers
    def _ensure_products_badge(self):
        try:
            if getattr(self, "_products_badge", None) is None and getattr(self, "btn_products", None) is not None:
                from PyQt6.QtWidgets import QLabel

                self._products_badge = QLabel(self.btn_products)
                self._products_badge.setStyleSheet(
                    """
                    QLabel {
                        background-color: #8B0000; /* dark red */
                        color: #ffffff;
                        border-radius: 10px;
                        padding: 1px 6px;
                        font-weight: 800;
                    }
                    """
                )
                self._products_badge.setVisible(False)
                self._products_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                self._products_badge.raise_()
        except Exception:
            pass

    def _position_products_badge(self):
        try:
            if getattr(self, "_products_badge", None) is None or getattr(self, "btn_products", None) is None:
                return
            badge = self._products_badge
            btn = self.btn_products
            # Ensure size hint is applied before positioning
            badge.adjustSize()
            x = max(0, btn.width() - badge.width() - 8)
            y = max(0, (btn.height() - badge.height()) // 2)
            badge.move(x, y)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            if obj is getattr(self, "btn_products", None) and event.type() == QEvent.Type.Resize:
                self._position_products_badge()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _tick_title_marquee(self):
        """Rotate the tagline in the window title to create a marquee effect."""
        try:
            base = getattr(self, "_title_base", APP_NAME) or APP_NAME
            tagline = getattr(self, "_tagline", "")
            if not tagline:
                self.setWindowTitle(base)
                return
            gap = "    "
            sequence = f"{tagline}{gap}"
            if len(sequence) == 0:
                self.setWindowTitle(base)
                return
            pos = getattr(self, "_marquee_pos", 0) or 0
            pos = pos % len(sequence)
            rotated = sequence[pos:] + sequence[:pos]
            self.setWindowTitle(f"{base} — {rotated}")
            self._marquee_pos = (pos + 1) % len(sequence)
        except Exception:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("admin", "Admin")
    window.show()
    sys.exit(app.exec())
