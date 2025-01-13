# Universal Navigation and Shipping Processing Service (UNSPS) Management Portal

## Overview
The UNSPS Management Portal is an end-to-end package tracking and management system. Designed for the fictional Universal Navigation and Shipping Processing Service (UNSPS) organization, it handles package entry, driver assignments, and delivery tracking. Users can follow a package's journey via its tracking number, viewing its status and history in real time.

You can try it out with a live demo at [dbp.mcallbos.co](https://dbp.mcallbos.co). 

---

## Features
- **Tracking Interface**: View the current status, delivery location, and history of packages.
- **Clerk Interface**: Enter package details and calculate shipping estimates.
- **Manager Interface**: Manage unassigned packages, assign drivers, and determine destinations.
- **Driver Interface**: Load assigned packages and mark them as delivered.
- **Responsive Design**: Optimized for desktop and mobile use, with auto light/dark mode.
- **Seamless Navigation**: Directly access the tracking page by appending `/trackingnumber` to the URL.

---

## Requirements
The UNSPS required a simple and efficient web application with the following capabilities:
1. **Package Entry**: Workers can easily input package details, including optional insurance, with pricing dynamically calculated based on the delivery distance.
2. **Delivery System**: Packages can be routed to either intermediate facilities or directly to the destination address.
3. **Tracking System**: End users can track their package in real-time, viewing its history, current status, and progress.

### Implementation Details
- **Address Management**: The system uses the xNAL (Extensible Name and Address Language) standard for storing and managing addresses in the database, ensuring compatibility and extensibility.
- **Inspiration**: 
  - The package entry screen was inspired by the Shippo interface for simplicity and usability.
  - The tracking page design drew inspiration from the USPS website, focusing on clarity and ease of use.
- **Limitations**:
  - Password authentication has not been implimented.
  - The distance a package travels is always 500 miles since we do not have a form of geolocation for addresses.
  - The map when a package is delivered will always show Fredonia University.

---

## Getting Started

### Prerequisites
- Python 3.12 or later.
- MySQL database for backend management.
- API key for IP geolocation (replace `INSERTKEYHERE` in `IPGEOLOCATIONKEY.SAMPLE.JSON` and rename to 'IPLGEOLOCATIONKEY.JSON').
  - This is required for timezone offsets, since Flet currently has not implimented a function to view a clients timezone.
  - This is a free API ['Check it out']("https://ipgeolocation.io/")

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/mcallbosco/DBProject.git
   cd DBProject
   ```
2. Configure the MySQL credentials in `MYSQLCREDS.SAMPLE.JSON` and rename the file to `MYSQLCREDS.JSON`.
3. Configure the geolocation API key in `IPGEOLOCATIONKEY.SAMPLE.JSON` and rename the file to `IPGEOLOCATIONKEY.JSON`
4. Install dependencies
5. Initialize the database using the scripts in `initNotebook.ipynb`.
6. Start the server:
   ```bash
   python main.py
   ```

---

## Usage
1. **Clerk Interface**: Log in with a clerk account (e.g., `clerk1`) to add packages.
2. **Manager Interface**: Use a manager account (e.g., `manager1`) to assign packages to drivers.
3. **Driver Interface**: Log in as a driver (e.g., `driver1`) to load and deliver packages.
4. **Tracking Interface**: End users can track packages by entering the tracking number.

---

## Demo
For a guided walkthrough, refer to `OnlineDemoREADME.md`, complete with screenshots and example workflows.

---
