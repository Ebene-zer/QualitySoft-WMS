# Wholesale-management-System 
# Dev: Ebenezer Fuachie
1.	Project Overview
The wholesale Management System is a desktop application designed to streamline wholesale business operations. It allows users to manage products, customers, orders, inventory, and reporting in a user-friendly environment.

3.	Objectives
•	Provide product, customer and invoice management
•	Generate useful reports (sales, inventory status)
•	Maintain records securely and efficiently

4.	Core features
   
3.1	Product Management
•	Add new products
•	Edit existing products
•	Delete products
•	List all products
•	Track stock quantity and prices
3.2	 Customer Management
•	Add new products
•	Edit customer details
•	Delete customer
•	View customer purchase history
3.3	 Order (Invoice) Management
•	Create new invoices
•	View and update invoices
•	Apply discounts and taxes
•	Automatically update stock levels
•	Print receipt for orders
3.4	Inventory Management
•	Monitor available stock
•	Alert for low stock items
3.5	Reports
•	Daily/weekly/monthly and annual sales reports
•	Inventory status reports
3.6	Authentication
•	Login. Role-based access (e.g., Admin, Manager, Clerk)
•	Logout

6.	System Architecture
NB: Developers guide
4.1	Technologies Used
•	Language: Python 3.13.2
•	IDE: PyCharm
•	UI Framework: PyQt6
•	Data storage: SQLite
•	Architecture Style: Modular (MVC-inspired)
Also, requirement text file will be included in the project
7.	Project Structure
NB: Developer's guide 
wholesale_management/
├── main.py
├── models/
│        ├── product.py
│        ├── customer.py
│         └── order.py
├── database/
│        ├── db_handler.py
├── ui/
│         └── gui.py
├── utils/
│         └── helpers.py
 └── docs/
           └── README.md
NB: This is just an initial structure and there can be improvement
8.	Testing & Validation
•	Manual testing for each module
•	Automated unit tests (later stage)
9.	Future Enhancements
•	Export reports to Excel/PDF
•	SMS notifications on receipt for orders
•	Cloud sync or remote DB support 
•	Barcode scanning


