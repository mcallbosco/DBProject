import flet as ft
import mysql.connector
import time

#It's definitly used for localizing and not for when we switch from this name
cName = "United Not States Postal Service"
cCode = "UNSPS"

mydb = mysql.connector.connect(
        host="localhost",
        port="3307",
        user= "root",
        password="RaNSEneyHYrO",
    )
mycursor = mydb.cursor(buffered=True, dictionary=True)
mycursor.execute("USE shipping")

def main(page: ft.Page):
    page.title = cCode + "Login"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    spawnLogin(page)
def displayIDProperly(id):
        return str(id) + str((int(id[0])+int(id[1])+int(id[2])+int(id[3])+int(id[4])+int(id[5])+int(id[6])+int(id[7])+int(id[8])+int(id[9]))).zfill(3)[1:3]

    
def spawnLogin(page: ft.Page):
    def login_click(e):
        valid = True
        typeOfUser = "Driver" #We will grab this from the user database if we end up doing that
        mycursor.execute(f"SELECT * FROM accounts WHERE username = '{txtf_username.value}'")
        user = mycursor.fetchone()
        if user == None:
            valid = False
        else:
            typeOfUser = user['roll']
        if valid:
            match typeOfUser:
                case "Manager":
                    #clear the page
                    page.remove(loginPage)
                    spawnManager(page, user)
                case "Driver":
                    page.remove(loginPage)
                    spawnDriver(page, user)
                case "Clerk":
                    page.remove(loginPage)
                    spawnClerk(page, user)
                case _:
                    print("Unimplimented user type")
        else:
            txt_invalid.value = "Invalid Username or Password"
            txtf_password.border_color = ft.colors.RED
            txtf_username.border_color = ft.colors.RED
            page.update()
    txtf_username = ft.TextField(text_align=ft.TextAlign.LEFT, width=300, on_submit=login_click)
    txtf_username.label = "Username"
    txtf_password = ft.TextField(text_align=ft.TextAlign.LEFT, width=300)
    txtf_password.label = "Password"
    txtf_password.password = True
    but_login = ft.FilledTonalButton("Login")
    image = ft.Image(src = f"/res/logoTemp.png")
    txt_invalid = ft.Text("   ", color=ft.colors.RED)
    loginPage = ft.Column(
            [
                image,
                txtf_username,
                txtf_password,
                txt_invalid,
                ft.Row(
                [but_login],
                alignment=ft.MainAxisAlignment.END,
                width=300 
            )
            ],
            alignment=ft.MainAxisAlignment.CENTER,

        )

    def textChange(e):
        if txt_invalid.value != "   ":
            txt_invalid.value = "   "
            txtf_password.border_color = ft.colors.BLACK   
            txtf_username.border_color = ft.colors.BLACK
            page.update()
    
    but_login.on_click = login_click
    txtf_username.on_change = textChange
    txtf_password.on_change = textChange
    page.add(
        loginPage
    )
    txtf_username.focus()

def spawnManager(page: ft.Page, user):
    page.scroll = True
    screenWidth = page.width
    #List of all packages in the facility. When a package is clicked on, there will be a popup with details, and the ability to assign a package to the driver with a destination facility.
    mycursor.execute(f"SELECT * FROM ready_for_assignment where location = {user['facility_id']}")
    packages = mycursor.fetchall()
    assignmentPanel = ft.Column()
    assignmentView = ft.Container(content=ft.ExpansionTile(
                    title=ft.Text("Sitting Packages"),
                    affinity=ft.TileAffinity.LEADING,
                    initially_expanded=True,
                    controls=[
                        assignmentPanel
                    ],
                    
                    expand=True, width=screenWidth * 0.7),expand=True, alignment=ft.alignment.center, visible=False)
    unassignmentPanel = ft.ExpansionPanelList(
        controls=[])
    unassignmentView = ft.Container(content=ft.ExpansionTile(
                    title=ft.Text("Sitting Packages"),
                    affinity=ft.TileAffinity.LEADING,
                    initially_expanded=False,
                    controls=[
                        assignmentPanel
                    ],
                    
                    expand=True, width=screenWidth * 0.7),expand=True, alignment=ft.alignment.center, visible=False)
    listOfDrivers = []
    mycursor.execute(f"SELECT * FROM accounts WHERE roll = 'Driver' and facility_id = {user['facility_id']}")
    listOfDrivers = mycursor.fetchall()
    listOfLocations = []
    mycursor.execute(f"SELECT * FROM facilities")
    listOfLocations = mycursor.fetchall()

    
    listOfDriversDropDown = ft.Dropdown(on_change=lambda e: page.update())
    listOfDriversDropDown.label = "Driver"
    driverOptions = []
    for driver in listOfDrivers:
        driverOptions.append(ft.dropdown.Option(text=driver['username'], data=driver['id']))

    listOfDriversDropDown.options = driverOptions
    listOfDriversDropDown.value = driverOptions[0].data
    listOfLocationsDropDown = ft.Dropdown(on_change=lambda e: page.update())
    listOfLocationsDropDown.label = "Destination"
    locationOptions = []
    for location in listOfLocations:
        locationOptions.append(ft.dropdown.Option(text=location['name'], data=location['id']))
    listOfLocationsDropDown.options = locationOptions
    listOfLocationsDropDown.value = locationOptions[0].data

    def constructAddressString(address):
        addressString = ""
        #only use name, locality, administrative_area, postal_code
        if address['name_line'] != None:
            addressString += address['name_line'] + "\n"
        if address['locality'] != None:
            addressString += address['locality'] + ", "
        if address['administrative_area'] != None:
            addressString += address['administrative_area'] + " "
        if address['postal_code'] != None:
            addressString += address['postal_code']
        return addressString
    

    
    def assignPackage(e):
        selectedFacility = None
        for location in listOfLocations:
            if location['name'] == listOfLocationsDropDown.value:
                selectedFacility = location["id"]
        selectedUserID = ""
        for driver in listOfDrivers:
            if driver['username'] == listOfDriversDropDown.value:
                selectedUserID = driver["id"]

        if selectedFacility == None or selectedUserID == "":
            #popup to select a facility
            material_actions = [
                ft.TextButton(text="Close", on_click=lambda e: page.close(e.control.parent)),
                ]
            page.open(ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Please select a destination facility/driver."),
                actions=material_actions,
            ))
            return
        mycursor.execute(f"DELETE FROM ready_for_assignment WHERE package_id = {e.control.data}")
        mycursor.execute(f"INSERT INTO package_assignment (package_id, driver_id, from_facility_id, to_facility_id, status) VALUES ({e.control.data}, {selectedUserID}, {user['facility_id']}, {selectedFacility}, 1)")
        mydb.commit()
        mycursor.execute(f"UPDATE package SET time_of_dispatch = NOW() WHERE id = {e.control.data}")
        mydb.commit()
        for assignment in assignmentPanel.controls:
            print (assignment.title.controls[0].value)
            print (e.control.data)
            if assignment.title.controls[0].value == str(displayIDProperly(str(e.control.data))):
                assignmentPanel.controls.remove(assignment)
        page.update()

    def spawnHistory(e):
        for package in packages:
            addressString = ""
            mycursor.execute(f"SELECT * FROM destination_address WHERE id = {package['package_id']}")
            address = mycursor.fetchone()
            addressString = constructAddressString(address)
            assignmentPanel.controls.append(ft.ExpansionTile(
                title=ft.Row([
                    ft.Text(str(displayIDProperly(str(package['package_id'])))),
                ]),
                controls=[ft.Column([ft.Text("Details: "), ft.Text(addressString), ft.Row([ft.Text("Driver: "), listOfDriversDropDown]), ft.Row([ft.Text("Destination: "), listOfLocationsDropDown]), ft.FilledTonalButton("Assign", on_click=assignPackage, data=package['package_id'])])],
            ))

        assignmentView.visible = True
        page.update()

    page.add(assignmentView)
    spawnHistory(None)



def spawnDriver(page: ft.Page, user):
    page.scroll = True
    inTheMiddleOfSomething = False
    def constructAddressString(address):
            addressString = ""
            #only use name, locality, administrative_area, postal_code
            if address['name_line'] != None:
                addressString += address['name_line'] + "\n"
            if address['locality'] != None:
                addressString += address['locality'] + ", "
            if address['administrative_area'] != None:
                addressString += address['administrative_area'] + " "
            if address['postal_code'] != None:
                addressString += address['postal_code']
            return addressString
    def markAsDelivered(e, manualData = None):
                if manualData == None:
                    manualData = e.control.data
                mycursor.execute(f"SELECT * FROM package_assignment WHERE package_id = {manualData} and driver_id = {userID} and status = 2")
                assignmentDetails = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM package WHERE id = {manualData}")
                packageDetails = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM destination_address WHERE id = {manualData}")
                address = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM facilities WHERE id = {assignmentDetails['to_facility_id']}")
                destinationFacilityName = mycursor.fetchone()['name']

                def handle_delivery_conf(e):
                    if e.control.text == "Yes":
                        toFacilityID = assignmentDetails["to_facility_id"]
                        if toFacilityID == 0:
                            mycursor.execute("UPDATE package SET time_of_delivery = NOW() WHERE id = " + str(e.control.data))
                        else:
                            mycursor.execute(f"INSERT INTO ready_for_assignment (package_id, time_created, location) VALUES ({e.control.data}, NOW(), {toFacilityID})")
                        mycursor.execute(f"SELECT * FROM facilities WHERE id = {toFacilityID}")
                        facility = mycursor.fetchone()
                        status = facility["arrived_status_code"]
                        mycursor.execute(f"SELECT * FROM status_info WHERE id = {status}")
                        statusrow = mycursor.fetchone()
                        locationName = facility["name"]
                        if locationName == "Address":
                            locationName = "Listed Address"
                            
                        
                        mycursor.execute(f"Insert INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({e.control.data},{status}, NOW(), 0, 0, '{locationName}', {toFacilityID})")
                        mycursor.execute(f"UPDATE package_assignment SET status = 3 WHERE package_id = {e.control.data} and driver_id = {userID} and status = 2")
                        mydb.commit()
                    page.close(e.control.parent)
                    page.update()
                    if e.control.text == "Yes":
                        time.sleep(.2)
                        swapViews(1)
                yesbuttonforthing = ft.TextButton(text="Yes", on_click=handle_delivery_conf, data=manualData)

                #
                material_actions = [
                    ft.TextButton(text="No", on_click=handle_delivery_conf, data=manualData),
                    yesbuttonforthing,

                    ]
                page.open(ft.AlertDialog(
                        title=ft.Text("Confirm Delivery"),
                        content=ft.Text("Tracking number: " + displayIDProperly(str(manualData)) + "\n Package Address:\n" + constructAddressString(address) + "\n Destination Address:\n " + destinationFacilityName),
                        actions=material_actions,
                    ))
                yesbuttonforthing.focus()
    userID = user['id']

    def getLatestStatus(packageID):
        mycursor.execute(f"SELECT * FROM package_status WHERE package_id = {packageID} ORDER BY time_created DESC")
        return mycursor.fetchone()
    def markAllAsDelivered(e):
        def handle_mark_all(e):
            if e.control.text == "Yes":
                inTheMiddleOfSomething = True
                mycursor.execute(f"SELECT * FROM package_assignment WHERE driver_id = {userID} and status = 2")
                packagesToDeliver = mycursor.fetchall()
                page.close(e.control.parent)
                for package in packagesToDeliver:
                    markAsDelivered(None, manualData=package['package_id'])
                inTheMiddleOfSomething = False
                swapViews(1)
        #popup to confirm
        material_actions = [
        ft.TextButton(text="Yes", on_click=handle_mark_all),
        ft.TextButton(text="No", on_click=handle_mark_all),
        ]
        page.open(ft.AlertDialog(
            title=ft.Text("Mark all as delivered?"),
            content=ft.Text("Are you sure you want to mark all packages as delivered?"),
            actions=material_actions,
        ))
    

    def swapViews(e = None):
        if inTheMiddleOfSomething:
            return
        
        deliveryPanel = ft.ExpansionPanelList(controls=[])
        if e == None or e == 0:
            index = 0
        elif e == 1:
            index = 1
        else :
            index = e.control.selected_index
        #Logic for loading view
        if index == 0:

            mycursor.execute(f"SELECT * FROM package_assignment WHERE driver_id = {userID} and status = 1")
            page.clean()
            packagesAvaliableToDeliver = mycursor.fetchall()
            if len(packagesAvaliableToDeliver) == 0:
                page.add(ft.Text("You have no packages assigned to you."))
                page.update()
                return
            loadContainerContents = []
            checkboxes = []
            def loadMarkedPackages(e):
                for checkbox in checkboxes:
                    if checkbox.value:
                        mycursor.execute(f"SELECT * FROM package_assignment WHERE package_id = {checkbox.data}")
                        package = mycursor.fetchone()
                        mycursor.execute(f"SELECT * FROM package WHERE id = {checkbox.data}")
                        packageInfo = mycursor.fetchone()
                        if (package['to_facility_id'] == 0):
                            """Create Table package_status (
                                id INT PRIMARY KEY, 
                                package_id INT, 
                                status INT,
                                time_created TIMESTAMP,
                                location_x DECIMAL(6,4),
                                location_y DECIMAL(6,4),
                                location_name VARCHAR(255),
                                location_id INT
                            );"""
                            lastStatus = getLatestStatus(package['package_id'])
                            statusX = lastStatus['location_x']
                            statusY = lastStatus['location_y']
                            mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({package['package_id']}, 11, NOW(),{statusX} , {statusY}, '{lastStatus["location_name"]}', 0)")
                            mydb.commit()
                        else:
                            #left facility.
                            lastStatus = getLatestStatus(package['package_id'])
                            lastID = lastStatus['location_id']
                            mycursor.execute(f"SELECT * FROM facilities WHERE id = {package['from_facility_id']}")
                            facility = mycursor.fetchone()
                            nextStatus = facility["departed_status_code"]
                            mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({package['package_id']}, {nextStatus}, NOW(),0 , 0, '{facility["name"]}', {lastID})")
                            mydb.commit()
                        mycursor.execute(f"UPDATE package_assignment SET status = 2 WHERE package_id = {checkbox.data}")
                        mydb.commit()
                swapViews(0)
            for package in packagesAvaliableToDeliver:
                print(package)
                destinationSTR = ""
                if package['to_facility_id'] == 0:
                    destinationSTR = "Final Destination"
                else:
                    mycursor.execute(f"SELECT * FROM facilities WHERE id = {package['to_facility_id']}")
                    destinationSTR = mycursor.fetchone()['name']
                checkboxes.append(ft.Checkbox(label=displayIDProperly(str(package['package_id'])) + "     Destination: " + destinationSTR, data=package['package_id']))
            loadContainerContents.append(ft.Column(checkboxes))
            loadContainerContents.append(ft.FilledTonalButton("Load", on_click=loadMarkedPackages))
            page.add(ft.Column(loadContainerContents))
            page.update()
        #Logic for delivery view
        else:
            def unload(e):
                mycursor.execute(f"UPDATE package_assignment SET status = 1 WHERE package_id = {e.control.data} and driver_id = {userID} and status = 2")
                mydb.commit()
                swapViews(1)
            
            page.clean()
            mycursor.execute(f"SELECT * FROM package_assignment WHERE driver_id = {userID} and status = 2")
            packagesToDeliver = mycursor.fetchall()
            if len(packagesToDeliver) == 0:
                page.add(ft.Text("You have not loaded any packages.\n Please select the load tab to load packages to deliver."))
                page.update()
                return
            
            for package in packagesToDeliver:
                 addressToWrite = ""
                 if (package['to_facility_id'] != 0):
                    mycursor.execute(f"SELECT * from facilities WHERE id = {package['to_facility_id']}")
                    facility = mycursor.fetchone()
                    mycursor.execute(f"SELECT * FROM destination_address WHERE id = {facility['address_id']}")
                    address = mycursor.fetchone()
                    addressToWrite = constructAddressString(address)
                 else:
                    mycursor.execute(f"SELECT * FROM destination_address WHERE id = {package['package_id']}")
                    addressToWrite = constructAddressString(mycursor.fetchone())
                 deliveryPanel.controls.append(ft.ExpansionPanel(
                    header=ft.Row([
                        ft.Text(str(displayIDProperly(str(package['package_id'])))),
                    ]),
                    can_tap_header=True,
                    content=ft.Column([ft.Text("Deliver to: "), ft.Text(addressToWrite), ft.Button("Mark as delivered", data=package['package_id'], on_click=markAsDelivered), ft.Button("Unload", on_click = unload, data=package['package_id'])]),
                ))
            
           
            page.add(deliveryPanel)
            #on click bring up a popup to confirm and then call the function
            page.add(ft.FilledTonalButton("Mark all as delivered", on_click=markAllAsDelivered))
            page.update()
            
        page.update()
    page.title = "CupertinoNavigationBar Example"
    page.navigation_bar = ft.CupertinoNavigationBar(
        bgcolor=ft.Colors.AMBER_100,
        inactive_color=ft.Colors.GREY,
        active_color=ft.Colors.BLACK,
        on_change=swapViews,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.FRONT_LOADER, label="Load"),
            ft.NavigationBarDestination(icon=ft.Icons.COMMUTE, label="Deliver"),
        ]
    )


    #load container will be a list of packages that need to be loaded, check boxes to select them, and a button to confirm
    swapViews()


def spawnClerk(page: ft.Page, user):
    page.scroll = True
    userLocationID = user['facility_id']
    #get facility info
    mycursor.execute(f"SELECT * FROM facilities WHERE id = {userLocationID}")
    facility = mycursor.fetchone()

    #page to enter in package info. 
    """CREATE TABLE package (
    id INT PRIMARY KEY,
    width INT,    -- In centimeters
    length INT,     -- In centimeters
    height INT,   -- In centimeters
    weight INT,  -- In grams
    price DECIMAL(10, 2),  -- In dollars
    type INT,
    insurance_id INT,
    shipment_id INT,
    estimated_distance INT,
    estimated_time_from_dispatch INT,
    time_created TIMESTAMP,
    time_updated TIMESTAMP,
    time_of_dispatch TIMESTAMP,
    time_of_delivery TIMESTAMP,
    delivery_cordinates_x DECIMAL(6,4),
    delivery_cordinates_y DECIMAL(6,4),
    delivery_conformation VARCHAR(255)
    );"""
    """Create Table destination_address (
    id INT PRIMARY KEY,
    country VARCHAR(2),
    name_line VARCHAR(255),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    organisation_name VARCHAR(255),
    administrative_area VARCHAR(50),
    sub_administrative_area VARCHAR(50),
    locality VARCHAR(50),
    dependent_locality VARCHAR(50),
    postal_code VARCHAR(50),
    thoroughfare VARCHAR(255),
    premise VARCHAR(255),
    sub_premise VARCHAR(255)
    );"""
    page.title = "Clerk"
    def generateInsuranceTypeString(insuranceType):
        return insuranceType['name'] + " $" + "max: $" + str(insuranceType['max_coverage'])
    def generateid():
        mycursor.execute("SELECT MAX(id) FROM package")
        return mycursor.fetchone()['MAX(id)'] + 1
    def displayIDProperly(id):
        return str(id) + str((int(id[0])+int(id[1])+int(id[2])+int(id[3])+int(id[4])+int(id[5])+int(id[6])+int(id[7])+int(id[8])+int(id[9]))).zfill(3)[1:3]
    #get insurance types from insuranceType
    mycursor.execute("SELECT * FROM insurance_type")
    insuranceTypes = mycursor.fetchall()
    insuranceTypeOptions = []
    insuranceDropDown = ft.Dropdown()
    insuranceDropDown.label = "Insurance Type"
    insuranceTypeOptions.append(ft.dropdown.Option(text="None", data=0))
    for insuranceType in insuranceTypes:
        insuranceTypeOptions.append(ft.dropdown.Option(text=generateInsuranceTypeString(insuranceType), data=insuranceType['id']))
    dimensionTypeOptions = []
    dimensionDropDown = ft.Dropdown(width=60)
    dimensionDropDown.label = "unit"
    dimensionTypeOptions.append(ft.dropdown.Option(text="IN", data=2.54, key=0))
    dimensionTypeOptions.append(ft.dropdown.Option(text="FT", data=30.48, key=1))
    dimensionTypeOptions.append(ft.dropdown.Option(text="CM", data=1, key=2))
    lengthKey = {"0": "2.54", "1": "30.48", "2": "1"}
    dimensionDropDown.options = dimensionTypeOptions
    dimensionDropDown.value = 0


    #get shipment types from shipmentType
    mycursor.execute("SELECT * FROM shipment_type")
    shipmentTypes = mycursor.fetchall()
    shipmentTypeOptions = []
    shipmentDropDown = ft.Dropdown()
    shipmentDropDown.label = "Shipment Type"
    for shipmentType in shipmentTypes:
        shipmentTypeOptions.append(ft.dropdown.Option(text=shipmentType['name'], data=shipmentType['id']))
    shipmentDropDown.options = shipmentTypeOptions
    insuranceDropDown.options = insuranceTypeOptions
    packageWidthString = ft.Text("Dimensions: ")
    packageDimensionsSeperator = ft.Text(" x ")
    packageWidthField = ft.TextField(label="W", width=80,input_filter = ft.InputFilter('^[0-9]*$'), max_length=3)
    packageLengthField = ft.TextField(label="L", width=80,input_filter = ft.InputFilter('^[0-9]*$'), max_length=3)
    packageHeightField = ft.TextField(label="H", width=80,input_filter = ft.InputFilter('^[0-9]*$'), max_length=3)
    
    packageWeightString = ft.Text("Weight: ")
    packageWeightField = ft.TextField(input_filter = ft.InputFilter('^[0-9]*$'), max_length=5, width=80)
    packageWeightUnit = ft.Text("oz")
    packageInsuranceString = ft.Text("Insurance Type: ")
    packageInsuranceField = insuranceDropDown
    packageShipmentString = ft.Text("Shipment Type: ")
    packageShipmentField = shipmentDropDown

    packageFirstNameString = ft.Text("First Name: ")
    packageFirstNameField = ft.TextField(max_length=50)
    packageLastNameString = ft.Text("Last Name: ")
    packageLastNameField = ft.TextField(max_length=50)
    packageOrganisationString = ft.Text("Organisation: ")
    packageOrganisationField = ft.TextField(max_length=255)
    packageAdminAreaString = ft.Text("Administrative Area: ")
    packageAdminAreaField = ft.TextField(max_length=50)
    packageLocalityString = ft.Text("Locality: ")
    packageLocalityField = ft.TextField(max_length=50)
    packagePostalCodeString = ft.Text("Postal Code: ")
    packagePostalCodeField = ft.TextField(max_length=50)
    packageThoroughfareString = ft.Text("Thoroughfare: ")
    packageThoroughfareField = ft.TextField(max_length=255)
    packagePremiseString = ft.Text("Premise: ")
    packagePremiseField = ft.TextField(max_length=255)
    packageCountryString = ft.Text("Country: ")
    packageCountryField = ft.TextField(max_length = 2)
    packageDeclaredValueString = ft.Text("Declared Value: ")
    packageDeclaredValueField = ft.TextField(input_filter=ft.InputFilter('^[0-9]*$'), max_length=10)
    def initilizeFields(event):
        packageWidthField.focus()
        packageWidthField.value = ""
        packageLengthField.value = ""
        packageHeightField.value = ""
        packageWeightField.value = ""
        packageInsuranceField.value = "None"
        packageShipmentField.value = ""
        packageFirstNameField.value = ""
        packageLastNameField.value = ""
        packageOrganisationField.value = ""
        packageAdminAreaField.value = ""
        packageLocalityField.value = ""
        packagePostalCodeField.value = ""
        packageThoroughfareField.value = ""
        packagePremiseField.value = ""
        packageCountryField.value = ""
        packageDeclaredValueField.value = ""
        page.update()
    def addPackageTransaction(event):
        
        calculatedDistance = 500
        id = generateid()
        shipmentCost = 0
        shipmentTypeID = 0 
        shipmentID = packageShipmentField.value
        shipmentETA = 0
        for shipmentType in shipmentTypes:
            if shipmentType['name'] == shipmentID:
                shipmentTypeID = shipmentType['id']
                shipmentETA = float(shipmentType['days_per500Miles']) * calculatedDistance
                shipmentCost = shipmentType['cost_per500Miles']
        width = float(packageWidthField.value) * float(lengthKey[str(dimensionDropDown.value)])
        length = float(packageLengthField.value) * float(lengthKey[str(dimensionDropDown.value)])
        height = float(packageHeightField.value) * float(lengthKey[str(dimensionDropDown.value)])
        weight = float(packageWeightField.value) * 28.3495
        insuranceID = packageInsuranceField.value
        insuranceID = None
        insuranceIDFinal = 0
        insuranceRow = None
        for insuranceType in insuranceTypes:
            if insuranceType['id'] == insuranceID:
                insuranceRow = insuranceType
                insuranceIDFinal = insuranceType['id']
        if insuranceIDFinal != 0:
            insuranceCost = float(insuranceRow['cost_per500Miles']) * (calculatedDistance/500)

        shipmentID = packageShipmentField.value
        firstName = packageFirstNameField.value
        lastName = packageLastNameField.value
        organisation = packageOrganisationField.value
        adminArea = packageAdminAreaField.value
        locality = packageLocalityField.value
        postalCode = packagePostalCodeField.value
        thoroughfare = packageThoroughfareField.value
        premise = packagePremiseField.value
        country = packageCountryField.value
        declaredValue = packageDeclaredValueField.value
        mycursor.execute(f"INSERT INTO package (id, width, length, height, weight, price, type, insurance_id, shipment_id, estimated_distance, estimated_time_from_dispatch, time_created, time_updated, delivery_cordinates_x, delivery_cordinates_y, delivery_conformation) VALUES ({id}, {width}, {length},  {height}, {weight}, {shipmentCost}, 0, NULL, {shipmentTypeID}, {calculatedDistance}, {shipmentETA} , NOW(), NOW(), 42.4532, -79.3407, '')")
        
        mycursor.execute(f"INSERT INTO destination_address (id, country, name_line, first_name, last_name, organisation_name, administrative_area, locality, postal_code, thoroughfare, premise) VALUES ({id}, '{country}', '{firstName} {lastName}', '{firstName}', '{lastName}', '{organisation}', '{adminArea}', '{locality}', '{postalCode}', '{thoroughfare}', '{premise}')")
        if insuranceIDFinal != 0:
            mycursor.execute(f"INSERT INTO insurance (id, type, price, value_coverage) VALUES ({id}, {insuranceIDFinal}, insuranceCost, {declaredValue})")
        
        mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({id}, 1, NOW(), 0, 0, \"{facility["name"]}\", {user["facility_id"]})")
        mycursor.execute(f"INSERT INTO ready_for_assignment (package_id, time_created, location) VALUES ({id}, NOW(), {user["facility_id"]})")
        mydb.commit()
        page.close(event.control.parent)
        #popup with tracking number
        def okayAction(e):
            page.close(e.control.parent)
            initilizeFields(None)
        closeButton = ft.TextButton(text="OK", on_click=okayAction)
        material_actions = [
            closeButton, ft.TextButton(text="Copy Tracking Number", on_click=lambda e: page.set_clipboard(displayIDProperly(str(id)))),
            ]
        page.open(ft.AlertDialog(
            title=ft.Text("Package Added"),
            content=ft.Text("Tracking Number: " + displayIDProperly(str(id))),
            actions=material_actions,
            on_dismiss=initilizeFields,
        ))
        closeButton.focus()
    def generateEstimate(event):
        #check that all boxes are filled that are required
        if packageWidthField.value == "" or packageLengthField.value == "" or packageHeightField.value == "" or packageWeightField.value == "" or packageShipmentField.value == "" or packageFirstNameField.value == "" or packageLastNameField.value == "" or packageAdminAreaField.value == "" or packageLocalityField.value == "" or packagePostalCodeField.value == "" or packageThoroughfareField.value == "" or packageCountryField.value == "":
            material_actions = [
                ft.TextButton(text="Close", on_click=lambda e: page.close(e.control.parent)),
                ]
            page.open(ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text("Please fill out all required fields."),
                actions=material_actions,
            ))
            return
        calculatedDistance = 500 #this would be calculated based on address and route, but it is out of scope. 
        #put a popup with estimated distance, estimated insurance cost, estimated shipment cost, total cost and estimated time. 
        #get the insurance cost
        insuranceCost = 0
        insuranceID = packageInsuranceField.value
        for insuranceType in insuranceTypes:
            if generateInsuranceTypeString(insuranceType) == insuranceID:
                insuranceCost = float(insuranceType['cost_per500Miles']) * (calculatedDistance/500)
        for insuranceType in insuranceTypes:
            if insuranceType['id'] == insuranceID:
                insuranceCost = float(insuranceType['cost_per500Miles']) * (calculatedDistance/500)
        #get the shipment cost
        shipmentCost = 0
        shipmentID = packageShipmentField.value
        for shipmentType in shipmentTypes:
            if shipmentType['name'] == shipmentID:
                shipmentCost = float(shipmentType['cost_per500Miles']) * (calculatedDistance/500)

        
        #get the total cost
        totalCost = insuranceCost + shipmentCost
        #get the estimated time
        estimatedTime = 0
        for shipmentType in shipmentTypes:
            if shipmentType['id'] == shipmentID:
                estimatedTime = float(shipmentType['days_per500Miles']) * (calculatedDistance/500)

        if estimatedTime == 0:
            estimatedTime = 1
        #put a popup with estimated distance, estimated insurance cost, estimated shipment cost, total cost and estimated time.
        processButton = ft.TextButton(text="Process", on_click=addPackageTransaction)
        material_actions = [
            ft.TextButton(text="Cancel", on_click=lambda e: page.close(e.control.parent)),
            processButton,
        ]
        page.open(ft.AlertDialog(
            title=ft.Text("Estimated Costs"),
            content=ft.Text(f"Estimated Distance: {calculatedDistance:.2f} miles\nEstimated Insurance Cost: ${insuranceCost:.2f}\nEstimated Shipment Cost: ${shipmentCost:.2f}\nTotal Cost: ${totalCost:.2f}\nEstimated Time: {estimatedTime} days"),
            actions=material_actions,
        ))
        processButton.focus()
    def checkAdditionalOptions(event):
        if packageInsuranceField.value != "None" or None:
            #make sure there's a declared value
            if packageDeclaredValueField.value == "":
                material_actions = [
                    ft.TextButton(text="Close", on_click=spawnAdditionalOptions),
                    ]
                page.open(ft.AlertDialog(
                    title=ft.Text("Error"),
                    content=ft.Text("Please enter a declared value."),
                    actions=material_actions,
                ))
                return
        page.close(event.control.parent)
    def spawnAdditionalOptions(event):
        #popup with insurance options
        material_actions = [
            ft.TextButton(text="Close", on_click=checkAdditionalOptions ),
            ]
        page.open(ft.AlertDialog(
            title=ft.Text("Additional Options"),
            content=ft.Column([ft.Text("Insurance Options"), packageInsuranceField, ft.Text("Declared Value"), packageDeclaredValueField]),
            actions=material_actions,
        ))





    packageProcessButton = ft.FilledTonalButton("Estimate", on_click=generateEstimate)
    additionalInfoButton = ft.FilledTonalButton("Additional Options", on_click=spawnAdditionalOptions)


    inputContainer = ft.Column(
        [
            ft.Row([packageWidthString, packageWidthField, packageDimensionsSeperator, packageLengthField, packageDimensionsSeperator, packageHeightField, dimensionDropDown]),
            ft.Row([packageWeightString, packageWeightField, packageWeightUnit]),
            ft.Row([packageShipmentString, packageShipmentField]),
            ft.Row([packageFirstNameString, packageFirstNameField]),
            ft.Row([packageLastNameString, packageLastNameField]),
            ft.Row([packageOrganisationString, packageOrganisationField]),
            ft.Row([packageAdminAreaString, packageAdminAreaField]),
            ft.Row([packageLocalityString, packageLocalityField]),
            ft.Row([packagePostalCodeString, packagePostalCodeField]),
            ft.Row([packageThoroughfareString, packageThoroughfareField]),
            ft.Row([packagePremiseString, packagePremiseField]),
            ft.Row([packageCountryString, packageCountryField]),\
            additionalInfoButton,
            packageProcessButton
        ],
    )
    page.add(inputContainer)
    initilizeFields(None)


ft.app(main, view=ft.AppView.WEB_BROWSER)