# Thank you for trying out this project!

## Overview
This instance features 4 interfaces for the user to interact with the system:
1. Tracking interface. This is made for the end user to view the status of their package. 
2. Clerk interface. This is made for the clerk to enter a package into the system.
3. Manager interface. This is made for the manager to view the packages in their facility and assign them to a driver.
4. Driver interface. This is made for the driver to view the packages they need to deliver, and mark them as delivered.

In order to use this system, you will need to use on of the accounts listed at the bottom of the page. None of these accounts require a password, since this is a demo.

If you would like a guided demo with photos, skip to [`Guided Demo`](#-Guided-Demo)



## Getting Started
## Entering a package
First, you will need to log into a clerk account to enter a package into the system. "clerk1" is a clerk assigned to the "Chicago Distribution Center" that you may use. The address you use does not have to be valid, but you must enter all of the fields on the main page. The additional options button lets you enter insurance info. Press Estimate to get a shipping estimate, and press Submit to enter the package into the system. You can copy the tracking number into a text editor to save for later. The delivery distance is always entered in as 500 miles, so the estimates will always be the same. Ideally, this would get the distance between the two addresses, but this is not implimented due to it complicating the demo and requiring a valid address. If it was implimented, the price and delivery time would be calculated based on the distance using values in the database.


## Assigning a package
Next, you will need to log into a manager account to assign the package to a driver. "manager1" is a manager assigned to the "Chicago Distribution Center" that you can use. The manager interface will show all of the unassined packages in the facility that you can then assign. Your previously entered package should be in the list. Click on the package to assign it to a driver and a destination, which can either be the final address or another facility. Remeber the driver's name, since this will be the next user you log into. If you selected a facility, you should also remember it since you will need to log into a manager account at that facility to assign the package to a driver there. 

## Delivering a package
Finally, you will need to log into a driver account to deliver the package. "driver1" is a driver assigned to the "Chicago Distribution Center" that you can use. The driver interface will show all of the packages assigned to you. Click on the package to mark it as delivered. You can then log out. If you delivered it to the final address, you are finished. If you delivered it to another facility, you will need to log into a manager account at that facility to assign the package to a driver there. 

## Tracking a package
Tracking a package is simple. Just enter the tracking number and you can see the status of the package, a map of the delivery location when it's delivered, and the history of the package. The delivery chordinates are based on a placeholder always entered into the system, so the map will always show the same location. Ideally, this would get the geolocation of the driver when they mark a package as delivered, but this is not implimented due to it complicating the demo.


## Accounts
Here's a list of accounts based on the facility they are assigned to:
- Chicago Distribution Center
  - Clerk: clerk1
  - Manager: manager1
  - Driver: driver1, driver2, driver3
- LA Port Facility
    - Clerk: clerk2
    - Manager: manager2
    - Driver: driver4, driver5, driver6
- NYC Distribution Hub
    - Clerk: clerk3
    - Manager: manager3
    - Driver: driver7, driver8, driver9
- Dallas Sorting Center
    - Clerk: clerk4
    - Manager: manager4
    - Driver: driver10, driver11, driver12
- Phoenix Sorting Facility
    - Clerk: clerk5
    - Manager: manager5
    - Driver: driver13, driver14, driver15

## Guided Demo





