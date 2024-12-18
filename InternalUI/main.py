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

    

    
def spawnLogin(page: ft.Page):
    txtf_username = ft.TextField(text_align=ft.TextAlign.LEFT, width=300)
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
    def login_click(e):
        valid = True
        typeOfUser = "Driver" #We will grab this from the user database if we end up doing that
        print("Username: " + txtf_username.value)
        print("Password: " + txtf_password.value)
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
                    spawnManager(page)
                case "Driver":
                    page.remove(loginPage)
                    spawnDriver(page)
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

def spawnManager(page: ft.Page):
    pass

def spawnDriver(page: ft.Page):
    userID = 1
    def getLatestStatus(packageID):
        mycursor.execute(f"SELECT * FROM package_status WHERE package_id = {packageID} ORDER BY time_created DESC")
        return mycursor.fetchone()
    def markAllAsDelivered(e):
        def handle_mark_all(e):
            if e.control.text == "Yes":
                mycursor.execute(f"UPDATE package_assignment SET status = 3 WHERE driver_id = {userID} and status = 4")
                mydb.commit()
            page.close(e.control.parent)
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
        
        deliveryPanel = ft.ExpansionPanelList(controls=[])
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
            print (packagesAvaliableToDeliver)
            loadContainerContents = []
            checkboxes = []
            def loadMarkedPackages(e):
                for checkbox in checkboxes:
                    if checkbox.value:
                        mycursor.execute(f"SELECT * FROM package_assignment WHERE package_id = {checkbox.label}")
                        package = mycursor.fetchone()
                        mycursor.execute(f"SELECT * FROM package WHERE id = {checkbox.label}")
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
                            print (nextStatus)
                            print("running this")
                            mycursor.execute(f"INSERT INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({package['package_id']}, {nextStatus}, NOW(),0 , 0, '{facility["name"]}', {lastID})")
                            mydb.commit()
                        mycursor.execute(f"UPDATE package_assignment SET status = 2 WHERE package_id = {checkbox.label}")
                        mydb.commit()
                swapViews(0)
            for package in packagesAvaliableToDeliver:
                checkboxes.append(ft.Checkbox(label=f"{package['package_id']}"))
            loadContainerContents.append(ft.Column(checkboxes))
            loadContainerContents.append(ft.FilledTonalButton("Load", on_click=loadMarkedPackages))
            page.add(ft.Column(loadContainerContents))
            page.update()
        #Logic for delivery view
        else:
            def markAsDelivered(e):
                mycursor.execute(f"SELECT * FROM package_assignment WHERE package_id = {e.control.data}")
                assignmentDetails = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM package WHERE id = {e.control.data}")
                packageDetails = mycursor.fetchone()
                mycursor.execute(f"SELECT * FROM destination_address WHERE id = {e.control.data}")
                address = mycursor.fetchone()
                def handle_delivery_conf(e):
                    if e.control.text == "Yes":
                        toFacilityID = assignmentDetails["to_facility_id"]
                        mycursor.execute(f"SELECT * FROM facilities WHERE id = {toFacilityID}")
                        facility = mycursor.fetchone()
                        print (facility)
                        status = facility["arrived_status_code"]
                        mycursor.execute(f"SELECT * FROM status_info WHERE id = {status}")
                        statusrow = mycursor.fetchone()
                        locationName = facility["name"]
                        if locationName == "Address":
                            locationName = "Listed Address"
                            
                        
                        mycursor.execute(f"Insert INTO package_status (package_id, status, time_created, location_x, location_y, location_name, location_id) VALUES ({e.control.data},{status}, NOW(), 0, 0, '{locationName}', {toFacilityID})")
                        mycursor.execute(f"UPDATE package_assignment SET status = 3 WHERE package_id = {e.control.data}")
                        mydb.commit()
                    page.close(e.control.parent)
                    page.update()
                    if e.control.text == "Yes":
                        time.sleep(.2)
                        swapViews(1)
                #
                material_actions = [
                    ft.TextButton(text="Yes", on_click=handle_delivery_conf, data=e.control.data),
                    ft.TextButton(text="No", on_click=handle_delivery_conf, data=e.control.data),
                    ]
                page.open(ft.AlertDialog(
                        title=ft.Text("Confirm Delivery"),
                        content=ft.Text("Tracking number: " + str(e.control.data) + "\n " + constructAddressString(address)),
                        actions=material_actions,
                    ))
            def unload(e):
                mycursor.execute(f"UPDATE package_assignment SET status = 1 WHERE package_id = {e.control.data}")
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
                 deliveryPanel.controls.append(ft.ExpansionPanel(
                    header=ft.Row([
                        ft.Text(str(package['package_id'])),
                    ]),
                    content=ft.Column([ft.Text("Details: "), ft.Button("Mark as delivered", data=package['package_id'], on_click=markAsDelivered), ft.Button("Unload", on_click = unload, data=package['package_id'])]),
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
        return str(id) + str(id[0]+id[1]+id[2]+id[3]+id[4]+id[5]+id[6]+id[7]+id[8]+id[9])[-2:].zfill(2)
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
    dimensionTypeOptions.append(ft.dropdown.Option(text="CM", data=0, key=2))
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
    packageWidthField = ft.TextField(label="W", width=40)
    packageLengthField = ft.TextField(label="L", width=40)
    packageHeightField = ft.TextField(label="H", width=40)
    
    packageWeightString = ft.Text("Weight: ")
    packageWeightField = ft.TextField()
    packageTypeString = ft.Text("Shipment Type:")
    packageTypeField = ft.TextField()
    packageInsuranceString = ft.Text("Insurance Type: ")
    packageInsuranceField = insuranceDropDown
    packageShipmentString = ft.Text("Shipment Type: ")
    packageShipmentField = shipmentDropDown

    packageFirstNameString = ft.Text("First Name: ")
    packageFirstNameField = ft.TextField()
    packageLastNameString = ft.Text("Last Name: ")
    packageLastNameField = ft.TextField()
    packageOrganisationString = ft.Text("Organisation: ")
    packageOrganisationField = ft.TextField()
    packageAdminAreaString = ft.Text("Administrative Area: ")
    packageAdminAreaField = ft.TextField()
    packageLocalityString = ft.Text("Locality: ")
    packageLocalityField = ft.TextField()
    packagePostalCodeString = ft.Text("Postal Code: ")
    packagePostalCodeField = ft.TextField()
    packageThoroughfareString = ft.Text("Thoroughfare: ")
    packageThoroughfareField = ft.TextField()
    packagePremiseString = ft.Text("Premise: ")
    packagePremiseField = ft.TextField()
    packageSubPremiseString = ft.Text("Sub Premise: ")
    packageSubPremiseField = ft.TextField()
    packageCountryString = ft.Text("Country: ")
    packageCountryField = ft.TextField()
    packageDeclaredValueString = ft.Text("Declared Value: ")
    packageDeclaredValueField = ft.TextField()


    def generateEstimate(event):
        calculatedDistance = 500 #this would be calculated based on address and route, but it is out of scope. 
        #put a popup with estimated distance, estimated insurance cost, estimated shipment cost, total cost and estimated time. 
        #get the insurance cost
        insuranceCost = 0
        insuranceID = packageInsuranceField.value
        for insuranceType in insuranceTypes:
            if generateInsuranceTypeString(insuranceType) == insuranceID:
                insuranceCost = insuranceType['cost_per500Miles']
        print(insuranceCost)
        for insuranceType in insuranceTypes:
            if insuranceType['id'] == insuranceID:
                insuranceCost = insuranceType['cost_per500Miles']
        #get the shipment cost
        shipmentCost = 0
        shipmentID = packageShipmentField.value
        for shipmentType in shipmentTypes:
            if shipmentType['id'] == shipmentID:
                shipmentCost = shipmentType['cost_per500Miles']
        #get the total cost
        totalCost = insuranceCost + shipmentCost
        #get the estimated time
        estimatedTime = 0
        for shipmentType in shipmentTypes:
            if shipmentType['id'] == shipmentID:
                estimatedTime = shipmentType['days_per500Miles']
        if estimatedTime == 0:
            estimatedTime = 1
        #put a popup with estimated distance, estimated insurance cost, estimated shipment cost, total cost and estimated time.
        material_actions = [
            ft.TextButton(text="Cancel", on_click=lambda e: page.close(e.control.parent)),
            ft.TextButton(text="Process"),
        ]
        page.open(ft.AlertDialog(
            title=ft.Text("Estimated Costs"),
            content=ft.Text("Estimated Distance: " + str(calculatedDistance) + " miles\n" + "Estimated Insurance Cost: $" + str(insuranceCost) + "\nEstimated Shipment Cost: $" + str(shipmentCost) + "\nTotal Cost: $" + str(totalCost) + "\nEstimated Time: " + str(estimatedTime) + " days"),
            actions=material_actions,
        ))

    def spawnAdditionalOptions(event):
        #popup with insurance options
        material_actions = [
            ft.TextButton(text="Close", on_click=lambda e: page.close(e.control.parent)),
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
            ft.Row([packageTypeString, packageTypeField]),
            ft.Row([packageShipmentString, packageShipmentField]),
            ft.Row([packageFirstNameString, packageFirstNameField]),
            ft.Row([packageLastNameString, packageLastNameField]),
            ft.Row([packageOrganisationString, packageOrganisationField]),
            ft.Row([packageOrganisationString, packageOrganisationField]),
            ft.Row([packageAdminAreaString, packageAdminAreaField]),
            ft.Row([packageLocalityString, packageLocalityField]),
            ft.Row([packagePostalCodeString, packagePostalCodeField]),
            ft.Row([packageThoroughfareString, packageThoroughfareField]),
            ft.Row([packagePremiseString, packagePremiseField]),
            ft.Row([packageSubPremiseString, packageSubPremiseField]),
            ft.Row([packageCountryString, packageCountryField]),\
            additionalInfoButton,
            packageProcessButton
        ],
    )
    page.add(inputContainer)
    

    
        


ft.app(main, view=ft.AppView.WEB_BROWSER)